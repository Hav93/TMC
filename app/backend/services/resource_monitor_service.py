"""
资源监控服务

监控消息中的资源链接，提取115/磁力/ed2k链接，自动转存到115网盘
"""
import json
import hashlib
import re
from datetime import timedelta
from typing import List, Dict, Optional, TYPE_CHECKING
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from log_manager import get_logger
from database import get_db
from models import ResourceMonitorRule, ResourceRecord
from timezone_utils import get_user_now

if TYPE_CHECKING:
    from services.message_context import MessageContext

logger = get_logger("resource_monitor", "enhanced_bot.log")


class LinkExtractor:
    """链接提取器"""
    
    PATTERNS = {
        'pan115': [
            r'https?://(?:115|115cdn)\.com/s/[a-zA-Z0-9]+(?:\?password=[a-zA-Z0-9]+)?',
            r'115://[a-zA-Z0-9]+',
        ],
        'magnet': [
            r'magnet:\?xt=urn:btih:[a-zA-Z0-9]{32,40}[^\s]*',
        ],
        'ed2k': [
            r'ed2k://\|file\|[^\|]+\|[0-9]+\|[a-fA-F0-9]{32}\|[^\s]*',
        ]
    }
    
    @classmethod
    def extract_all(cls, text: str) -> Dict[str, List[str]]:
        """提取所有类型的链接"""
        results = {}
        for link_type, patterns in cls.PATTERNS.items():
            links = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                links.extend(matches)
            
            if links:
                results[link_type] = list(set(links))  # 去重
        
        return results
    
    @classmethod
    def calculate_hash(cls, link: str) -> str:
        """计算链接哈希（用于去重）"""
        return hashlib.md5(link.encode()).hexdigest()


class ResourceMonitorService:
    """
    资源监控服务
    
    功能：
    1. 监控消息中的资源链接
    2. 提取115/磁力/ed2k链接
    3. 自动转存到115网盘
    4. 去重和标签管理
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_active_rules_for_chat(self, chat_id: int) -> List[ResourceMonitorRule]:
        """获取聊天的活跃规则"""
        result = await self.db.execute(
            select(ResourceMonitorRule).where(
                ResourceMonitorRule.is_active == True
            )
        )
        all_rules = result.scalars().all()
        
        # 过滤匹配的规则
        matched_rules = []
        for rule in all_rules:
            source_chats = json.loads(rule.source_chats) if rule.source_chats else []
            source_chat_ids = [int(c) for c in source_chats]
            
            if int(chat_id) in source_chat_ids:
                matched_rules.append(rule)
                logger.debug(f"✅ 规则 '{rule.name}' 匹配聊天 {chat_id}")
        
        return matched_rules
    
    async def handle_new_message(self, context: 'MessageContext'):
        """
        处理新消息
        
        流程：
        1. 获取适用的规则
        2. 提取链接
        3. 关键词过滤
        4. 去重检查
        5. 创建记录
        6. 自动转存（如果启用）
        """
        try:
            # 1. 获取规则
            rules = await self.get_active_rules_for_chat(context.chat_id)
            if not rules:
                logger.debug(f"聊天 {context.chat_id} 没有活跃的资源监控规则")
                return
            
            logger.info(f"📊 找到 {len(rules)} 个资源监控规则")
            
            # 2. 提取链接
            links = await context.get_extracted_links()
            if not links:
                logger.debug("消息中未找到链接")
                return
            
            logger.info(f"🔗 提取到链接: {links}")
            
            # 3. 处理每个规则
            for rule in rules:
                await self._process_rule(context, rule, links)
                
        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)
    
    async def _process_rule(self, context: 'MessageContext', rule: ResourceMonitorRule, links: Dict[str, List[str]]):
        """处理单个规则"""
        try:
            # 1. 关键词过滤
            if rule.keywords:
                keywords = json.loads(rule.keywords)
                keyword_list = [k.get('keyword', '') for k in keywords if not k.get('is_exclude', False)]
                exclude_keywords = [k.get('keyword', '') for k in keywords if k.get('is_exclude', False)]
                
                # 检查排除关键词
                message_text = (context.message.text or "").lower()
                for exclude_keyword in exclude_keywords:
                    if exclude_keyword.lower() in message_text:
                        logger.info(f"规则 {rule.name} 命中排除关键词: {exclude_keyword}")
                        return
                
                # 检查包含关键词
                if keyword_list:
                    matched = await context.get_matched_keywords(keyword_list)
                    if not matched:
                        logger.info(f"规则 {rule.name} 关键词不匹配")
                        return
            
            # 2. 链接类型过滤
            link_types = json.loads(rule.link_types) if rule.link_types else []
            
            # 3. 处理每个链接
            for link_type in link_types:
                if link_type not in links:
                    continue
                
                for link_url in links[link_type]:
                    await self._process_link(context, rule, link_type, link_url)
                    
        except Exception as e:
            logger.error(f"处理规则 {rule.name} 失败: {e}", exc_info=True)
    
    async def _process_link(self, context: 'MessageContext', rule: ResourceMonitorRule, 
                           link_type: str, link_url: str):
        """处理单个链接"""
        try:
            # 1. 去重检查
            link_hash = LinkExtractor.calculate_hash(link_url)
            
            if rule.enable_deduplication:
                if await self._is_duplicate(link_hash, rule.dedup_time_window):
                    logger.info(f"链接已存在（去重）: {link_url[:50]}...")
                    return
            
            # 2. 创建记录
            record = await self._create_record(context, rule, link_type, link_url, link_hash)
            
            # 3. 自动处理（统一路由 + 变量渲染 + 类型专属路径覆盖）
            # 规则可选字段：target_path_pan115 / target_path_magnet / target_path_ed2k
            override_path = getattr(rule, f"target_path_{link_type}", None) if hasattr(rule, f"target_path_{link_type}") else None
            if rule.auto_save_to_115 and link_type == 'pan115':
                await self._auto_save_to_115(record, rule, context, override_path)
            if link_type in ('magnet', 'ed2k'):
                await self._auto_offline_via_clouddrive2(record, rule, context, override_path)
                
        except Exception as e:
            logger.error(f"处理链接失败: {e}", exc_info=True)
    
    async def _is_duplicate(self, link_hash: str, time_window: int) -> bool:
        """检查链接是否重复"""
        cutoff_time = get_user_now() - timedelta(seconds=time_window)
        
        result = await self.db.execute(
            select(ResourceRecord).where(
                and_(
                    ResourceRecord.link_hash == link_hash,
                    ResourceRecord.created_at >= cutoff_time
                )
            ).limit(1)
        )
        
        return result.scalar_one_or_none() is not None
    
    async def _create_record(self, context: 'MessageContext', rule: ResourceMonitorRule,
                            link_type: str, link_url: str, link_hash: str) -> ResourceRecord:
        """创建资源记录"""
        from timezone_utils import telegram_time_to_user_time
        
        # 获取默认标签
        default_tags = json.loads(rule.default_tags) if rule.default_tags else []
        
        # 转换消息时间到用户时区
        user_time = telegram_time_to_user_time(context.message.date)
        
        # 创建消息快照
        message_snapshot = {
            'id': context.message.id,
            'date': user_time.isoformat() if user_time else None,
            'text': context.message.text or "",
            'chat_id': context.chat_id
        }
        
        record = ResourceRecord(
            rule_id=rule.id,
            rule_name=rule.name,
            source_chat_id=str(context.chat_id),
            message_id=context.message.id,
            message_text=context.message.text or "",
            message_date=user_time,
            link_type=link_type,
            link_url=link_url,
            link_hash=link_hash,
            save_status='pending',
            tags=json.dumps(default_tags, ensure_ascii=False),
            message_snapshot=json.dumps(message_snapshot, ensure_ascii=False)
        )
        
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        
        logger.info(f"✅ 创建资源记录: ID={record.id}, 类型={link_type}, 链接={link_url[:50]}...")
        return record
    
    def _get_cd2_api_root(self) -> str:
        """读取 CloudDrive2 在线根（优先 CLOUDDRIVE2_API_ROOT，否则从 MOUNT_POINT 推导）。"""
        import os
        api_root = os.getenv('CLOUDDRIVE2_API_ROOT', '').strip()
        if api_root:
            return api_root if api_root.startswith('/') else '/' + api_root
        mount_point = os.getenv('CLOUDDRIVE2_MOUNT_POINT', '').strip()
        if mount_point.startswith('/CloudNAS/'):
            return '/' + mount_point.split('/')[-1]
        return '/115open'

    def _expand_variables(self, pattern: str, context: 'MessageContext', rule: ResourceMonitorRule) -> str:
        """展开 {YYYY}/{MM}/{DD}/{chat}/{rule} 变量。"""
        try:
            now = get_user_now()
            mapping = {
                'YYYY': f"{now.year:04d}",
                'MM': f"{now.month:02d}",
                'DD': f"{now.day:02d}",
                'chat': str(context.chat_id),
                'rule': rule.name or 'rule'
            }
            out = pattern or ''
            for k, v in mapping.items():
                out = out.replace('{' + k + '}', v)
            return out
        except Exception:
            return pattern or ''

    def _normalize_relative_path(self, path: str, api_root: str) -> str:
        """规范为相对层级：剥离 /CloudNAS/<root> 或 api_root。"""
        p = (path or '').replace('\\', '/').strip()
        if not p:
            return ''
        if p.startswith('/'):
            if p.startswith('/CloudNAS/'):
                parts = p.split('/')
                p = '/'.join(parts[3:])
            elif api_root and p.startswith(api_root.rstrip('/') + '/'):
                p = p[len(api_root.rstrip('/')) + 1:]
            elif api_root and p == api_root:
                p = ''
            else:
                p = p.lstrip('/')
        return p.strip('/')

    def _compute_final_paths(self, raw_target_path: str, context: 'MessageContext', rule: ResourceMonitorRule) -> Dict[str, str]:
        """返回 {'relative','cd2_folder','pan115_folder'}"""
        api_root = self._get_cd2_api_root()
        expanded = self._expand_variables(raw_target_path or '', context, rule)
        rel = self._normalize_relative_path(expanded, api_root)
        pan115_folder = '/' + rel if rel else '/'
        cd2_folder = (api_root.rstrip('/') + '/' + rel).rstrip('/') if rel else api_root
        return {'relative': rel, 'cd2_folder': cd2_folder, 'pan115_folder': pan115_folder}

    async def _auto_save_to_115(self, record: ResourceRecord, rule: ResourceMonitorRule, context: 'MessageContext', override_path: str | None = None):
        """自动转存到115"""
        try:
            # 更新状态为"转存中"
            record.save_status = 'saving'
            await self.db.commit()
            
            logger.info(f"⚡ 开始115转存: record_id={record.id}")
            
            # 提取分享码
            match = re.search(r'/s/([a-zA-Z0-9]+)', record.link_url)
            if not match:
                raise ValueError("无法提取分享码")
            
            share_code = match.group(1)
            
            # 提取密码（如果有）
            password_match = re.search(r'password=([a-zA-Z0-9]+)', record.link_url)
            receive_code = password_match.group(1) if password_match else None
            
            logger.info(f"📋 转存参数: share_code={share_code}, receive_code={receive_code}, target_path={rule.target_path}")
            
            # 调用115转存API
            from services.pan115_client import Pan115Client
            from models import MediaSettings
            from sqlalchemy import select
            
            # 获取115配置
            settings_result = await self.db.execute(select(MediaSettings))
            settings = settings_result.scalars().first()
            
            if not settings:
                raise ValueError("未找到115网盘配置")
            
            user_id = getattr(settings, 'pan115_user_id', None)
            user_key = getattr(settings, 'pan115_user_key', None)
            
            if not user_id or not user_key:
                raise ValueError("请先登录115网盘")
            
            # 创建115客户端（仅使用Web API）
            client = Pan115Client(
                app_id="",  # 使用Web API
                app_key="",
                user_id=user_id,
                user_key=user_key,
                use_proxy=getattr(settings, 'pan115_use_proxy', False)
            )
            
            # 统一路由 + 变量展开（支持类型专属覆盖）
            raw_path = override_path if (override_path and str(override_path).strip() != '') else (rule.target_path or '/')
            routed = self._compute_final_paths(raw_path, context, rule)
            target_path = routed['pan115_folder']
            target_dir_id = "0"  # 默认根目录
            
            if target_path and target_path != "/":
                # 创建目录路径并获取目录ID
                logger.info(f"📁 创建目标目录: {target_path}")
                dir_result = await client.create_directory_path(target_path)
                
                if dir_result.get('success'):
                    target_dir_id = dir_result.get('dir_id', '0')
                    logger.info(f"✅ 目标目录ID: {target_dir_id}")
                else:
                    logger.warning(f"⚠️ 创建目录失败，使用根目录: {dir_result.get('message')}")
            
            # 调用转存API
            save_result = await client.save_share(
                share_code=share_code,
                receive_code=receive_code,
                target_dir_id=target_dir_id
            )
            
            if save_result.get('success'):
                saved_count = save_result.get('saved_count', 0)
                
                # 检查是否为重复
                if save_result.get('duplicate'):
                    logger.info(f"⚠️ 115转存重复: record_id={record.id}, 文件已存在")
                    record.save_status = 'duplicate'
                    record.save_path = target_path or "/"
                    record.save_time = get_user_now()
                    record.save_error = "文件已存在（之前已转存）"
                else:
                    logger.info(f"✅ 115转存成功: record_id={record.id}, 转存了{saved_count}个文件")
                    record.save_status = 'success'
                    record.save_path = target_path or "/"
                    record.save_time = get_user_now()
                
                await self.db.commit()
            else:
                error_msg = save_result.get('message', '转存失败')
                raise ValueError(error_msg)
            
        except Exception as e:
            logger.error(f"115转存失败: {e}", exc_info=True)
            
            # 更新失败状态
            record.save_status = 'failed'
            record.save_error = str(e)
            record.retry_count += 1
            await self.db.commit()
            
            # 加入重试队列
            try:
                from services.common.retry_queue import get_retry_queue, RetryStrategy
                retry_queue = get_retry_queue()
                
                await retry_queue.add_task(
                    task_id=f"115_save_{record.id}",
                    task_type="resource_115_save",
                    task_data={
                        'record_id': record.id,
                        'rule_id': rule.id,
                        'share_code': share_code,
                        'receive_code': receive_code,
                        'target_path': target_path
                    },
                    max_retries=3,
                    strategy=RetryStrategy.EXPONENTIAL,
                    base_delay=300  # 5分钟
                )
                logger.info(f"已加入重试队列: record_id={record.id}")
            except Exception as retry_error:
                logger.error(f"加入重试队列失败: {retry_error}")

    async def _auto_offline_via_clouddrive2(self, record: ResourceRecord, rule: ResourceMonitorRule, context: 'MessageContext', override_path: str | None = None):
        """磁力/ed2k 通过 CloudDrive2 添加离线任务"""
        try:
            # 目标目录：规则 target_path 作为相对路径拼到 CloudDrive2 默认根
            from services.clouddrive2_client import create_clouddrive2_client
            import os

            client = create_clouddrive2_client()
            await client.connect()

            # 统一路由（绝对CD2目录）- 支持类型专属覆盖
            raw_path = override_path if (override_path and str(override_path).strip() != '') else (rule.target_path or '/')
            routed = self._compute_final_paths(raw_path, context, rule)
            to_folder = routed['cd2_folder']

            # 提交离线任务
            logger.info(f"⚡ 提交离线任务: url={record.link_url[:60]}..., folder={to_folder}")
            res = await client.add_offline_file(record.link_url, to_folder)
            await client.disconnect()

            if res.get('success'):
                record.save_status = 'queued'
                record.save_path = res.get('folder') or to_folder
                record.save_time = get_user_now()
                record.save_error = None
                await self.db.commit()
                logger.info(f"✅ 已提交离线任务: record_id={record.id}")
            else:
                raise ValueError(res.get('message', '提交离线任务失败'))

        except Exception as e:
            logger.error(f"CloudDrive2 离线任务失败: {e}", exc_info=True)
            record.save_status = 'failed'
            record.save_error = str(e)
            record.retry_count += 1
            await self.db.commit()


# 创建资源监控处理器
from services.message_dispatcher import MessageProcessor

class ResourceMonitorProcessor(MessageProcessor):
    """资源监控消息处理器"""
    
    def __init__(self):
        """不需要传入数据库会话，每次处理时动态获取"""
        pass
    
    async def should_process(self, context: 'MessageContext') -> bool:
        """判断是否应该处理这条消息"""
        # 每次处理时获取新的数据库会话
        async for db in get_db():
            service = ResourceMonitorService(db)
            rules = await service.get_active_rules_for_chat(context.chat_id)
            return len(rules) > 0
        return False
    
    async def process(self, context: 'MessageContext') -> bool:
        """处理消息"""
        try:
            # 每次处理时获取新的数据库会话
            async for db in get_db():
                service = ResourceMonitorService(db)
                await service.handle_new_message(context)
                break
            return True
        except Exception as e:
            logger.error(f"ResourceMonitorProcessor 处理失败: {e}", exc_info=True)
            return False


# ===== 重试处理器 =====

async def handle_115_save_retry(task) -> bool:
    """处理115转存重试任务"""
    from services.common.retry_queue import RetryTask
    
    try:
        record_id = task.task_data['record_id']
        rule_id = task.task_data['rule_id']
        share_code = task.task_data['share_code']
        receive_code = task.task_data.get('receive_code')
        target_path = task.task_data.get('target_path', '/')
        
        logger.info(f"🔄 重试115转存: record_id={record_id}, 重试次数={task.retry_count}")
        
        # 获取数据库会话
        async for db in get_db():
            # 获取记录
            record = await db.get(ResourceRecord, record_id)
            if not record:
                logger.error(f"记录不存在: record_id={record_id}")
                return False
            
            # 更新状态
            record.save_status = 'saving'
            record.retry_count = task.retry_count
            await db.commit()
            
            # 提取分享码和密码
            import re
            match = re.search(r'/s/([a-zA-Z0-9]+)', record.link_url)
            if not match:
                raise ValueError("无法提取分享码")
            
            share_code = match.group(1)
            password_match = re.search(r'password=([a-zA-Z0-9]+)', record.link_url)
            receive_code = password_match.group(1) if password_match else None
            
            # 调用115转存API
            from services.pan115_client import Pan115Client
            from models import MediaSettings
            from sqlalchemy import select
            
            # 获取115配置
            settings_result = await db.execute(select(MediaSettings))
            settings = settings_result.scalars().first()
            
            if not settings:
                raise ValueError("未找到115网盘配置")
            
            user_id = getattr(settings, 'pan115_user_id', None)
            user_key = getattr(settings, 'pan115_user_key', None)
            
            if not user_id or not user_key:
                raise ValueError("请先登录115网盘")
            
            # 创建115客户端（仅使用Web API）
            client = Pan115Client(
                app_id="",  # 使用Web API
                app_key="",
                user_id=user_id,
                user_key=user_key,
                use_proxy=getattr(settings, 'pan115_use_proxy', False)
            )
            
            # 获取或创建目标目录
            target_dir_id = "0"  # 默认根目录
            
            if target_path and target_path != "/":
                # 创建目录路径并获取目录ID
                logger.info(f"📁 重试: 创建目标目录: {target_path}")
                dir_result = await client.create_directory_path(target_path)
                
                if dir_result.get('success'):
                    target_dir_id = dir_result.get('dir_id', '0')
                    logger.info(f"✅ 重试: 目标目录ID: {target_dir_id}")
                else:
                    logger.warning(f"⚠️ 重试: 创建目录失败，使用根目录: {dir_result.get('message')}")
            
            # 调用转存API
            save_result = await client.save_share(
                share_code=share_code,
                receive_code=receive_code,
                target_dir_id=target_dir_id
            )
            
            if save_result.get('success'):
                saved_count = save_result.get('saved_count', 0)
                
                # 检查是否为重复
                if save_result.get('duplicate'):
                    logger.info(f"⚠️ 重试转存重复: record_id={record_id}, 文件已存在")
                    record.save_status = 'duplicate'
                    record.save_path = target_path
                    record.save_time = get_user_now()
                    record.save_error = "文件已存在（之前已转存）"
                else:
                    logger.info(f"✅ 重试转存成功: record_id={record_id}, 转存了{saved_count}个文件")
                    record.save_status = 'success'
                    record.save_path = target_path
                    record.save_time = get_user_now()
                    record.save_error = None  # 清空之前的错误信息
                
                await db.commit()
                return True
            else:
                error_msg = save_result.get('message', '转存失败')
                logger.error(f"❌ 重试转存失败: record_id={record_id}, {error_msg}")
                
                # 标记为失败
                record.save_status = 'failed'
                record.save_error = error_msg
                await db.commit()
                return False
    
    except Exception as e:
        logger.error(f"重试失败: {e}", exc_info=True)
        return False


def register_retry_handlers():
    """注册重试处理器"""
    from services.common.retry_queue import get_retry_queue
    
    retry_queue = get_retry_queue()
    retry_queue.register_handler("resource_115_save", handle_115_save_retry)
    logger.info("✅ 注册资源监控重试处理器")

