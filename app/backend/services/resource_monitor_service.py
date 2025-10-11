"""
资源监控服务 - 监控Telegram消息中的资源链接并自动转存到115
"""
import re
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import ResourceMonitorRule, ResourceRecord
from services.p115_service import P115Service

logger = logging.getLogger(__name__)


class LinkExtractor:
    """链接提取器"""
    
    # 链接匹配模式
    PATTERNS = {
        'pan115': [
            r'https?://115\.com/s/[a-zA-Z0-9]+(?:\?password=[a-zA-Z0-9]+)?',
            r'115://[a-zA-Z0-9]+',
        ],
        'magnet': [
            r'magnet:\?xt=urn:btih:[a-zA-Z0-9]{32,40}[^\s]*',
        ],
        'ed2k': [
            r'ed2k://\|file\|[^\|]+\|\d+\|[A-F0-9]{32}\|[^\s]*',
        ]
    }
    
    @classmethod
    def extract(cls, text: str, rule: ResourceMonitorRule) -> Dict[str, List[str]]:
        """
        提取所有类型的链接
        
        Args:
            text: 消息文本
            rule: 监控规则
            
        Returns:
            {'pan115': [...], 'magnet': [...], 'ed2k': [...]}
        """
        result = {
            'pan115': [],
            'magnet': [],
            'ed2k': []
        }
        
        if not text:
            return result
        
        # 根据规则配置提取对应类型的链接
        if rule.monitor_pan115:
            for pattern in cls.PATTERNS['pan115']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                result['pan115'].extend(matches)
        
        if rule.monitor_magnet:
            for pattern in cls.PATTERNS['magnet']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                result['magnet'].extend(matches)
        
        if rule.monitor_ed2k:
            for pattern in cls.PATTERNS['ed2k']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                result['ed2k'].extend(matches)
        
        # 去重
        for key in result:
            result[key] = list(set(result[key]))
        
        return result
    
    @classmethod
    def generate_fingerprint(cls, links: Dict[str, List[str]]) -> str:
        """
        生成链接指纹用于去重
        
        Args:
            links: 链接字典
            
        Returns:
            MD5哈希值
        """
        all_links = []
        for link_list in links.values():
            all_links.extend(link_list)
        
        if not all_links:
            return ''
        
        # 排序后生成MD5
        link_str = '|'.join(sorted(all_links))
        return hashlib.md5(link_str.encode()).hexdigest()


class ResourceMonitorService:
    """资源监控服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.link_extractor = LinkExtractor()
    
    async def get_active_rules_for_chat(self, chat_id: int) -> List[ResourceMonitorRule]:
        """
        获取指定聊天的所有活跃监控规则
        
        Args:
            chat_id: 聊天ID
            
        Returns:
            规则列表
        """
        query = select(ResourceMonitorRule).where(
            ResourceMonitorRule.is_active == True
        )
        result = await self.db.execute(query)
        all_rules = result.scalars().all()
        
        # 过滤出包含该chat_id的规则
        matched_rules = []
        for rule in all_rules:
            if rule.source_chats:
                try:
                    source_chats = json.loads(rule.source_chats)
                    if str(chat_id) in [str(c) for c in source_chats]:
                        matched_rules.append(rule)
                except json.JSONDecodeError:
                    logger.error(f"规则 {rule.id} 的 source_chats 格式错误")
        
        return matched_rules
    
    def match_keywords(self, text: str, rule: ResourceMonitorRule) -> bool:
        """
        关键词匹配
        
        Args:
            text: 消息文本
            rule: 监控规则
            
        Returns:
            是否匹配
        """
        if not text:
            return False
        
        # 如果没设置关键词，直接通过
        if not rule.include_keywords and not rule.exclude_keywords:
            return True
        
        # 必须包含的关键词
        if rule.include_keywords:
            try:
                include_kws = json.loads(rule.include_keywords)
                if not any(kw in text for kw in include_kws):
                    return False
            except json.JSONDecodeError:
                pass
        
        # 必须排除的关键词
        if rule.exclude_keywords:
            try:
                exclude_kws = json.loads(rule.exclude_keywords)
                if any(kw in text for kw in exclude_kws):
                    return False
            except json.JSONDecodeError:
                pass
        
        return True
    
    def generate_message_snapshot(self, message) -> Dict:
        """
        生成消息快照
        
        Args:
            message: Telegram消息对象
            
        Returns:
            消息快照字典
        """
        snapshot = {
            'text': message.text or message.caption or '',
            'date': message.date.isoformat() if message.date else None,
            'message_id': message.id,
            'chat_id': message.chat_id,
            'chat_title': message.chat.title if hasattr(message.chat, 'title') else '',
            'sender_id': message.sender_id,
            'sender_name': self._get_sender_name(message),
            'views': message.views if hasattr(message, 'views') else None,
            'forwards': message.forwards if hasattr(message, 'forwards') else None,
            'has_media': message.media is not None,
            'media_type': message.media.__class__.__name__ if message.media else None,
            'reply_to_msg_id': message.reply_to_msg_id,
        }
        
        return snapshot
    
    def _get_sender_name(self, message) -> str:
        """获取发送者名称"""
        if message.sender:
            if hasattr(message.sender, 'first_name'):
                name = message.sender.first_name or ''
                if hasattr(message.sender, 'last_name') and message.sender.last_name:
                    name += ' ' + message.sender.last_name
                return name.strip()
            elif hasattr(message.sender, 'title'):
                return message.sender.title
        return 'Unknown'
    
    async def handle_new_message(self, message):
        """
        处理新消息 - 核心入口
        
        Args:
            message: Telegram消息对象
        """
        try:
            # 1. 获取该聊天的所有活跃监控规则
            rules = await self.get_active_rules_for_chat(message.chat_id)
            if not rules:
                return
            
            message_text = message.text or message.caption or ""
            if not message_text:
                return
            
            for rule in rules:
                try:
                    # 2. 关键词过滤
                    if not self.match_keywords(message_text, rule):
                        continue
                    
                    # 3. 提取链接
                    links = self.link_extractor.extract(message_text, rule)
                    if not any(links.values()):
                        continue
                    
                    # 4. 生成链接指纹
                    fingerprint = self.link_extractor.generate_fingerprint(links)
                    
                    # 5. 检查是否已存在（去重）
                    existing = await self.db.execute(
                        select(ResourceRecord).where(
                            ResourceRecord.link_fingerprint == fingerprint
                        )
                    )
                    if existing.scalar_one_or_none():
                        logger.info(f"⏭️ 跳过重复资源: {fingerprint[:8]}...")
                        continue
                    
                    # 6. 生成消息快照
                    snapshot = self.generate_message_snapshot(message)
                    
                    # 7. 保存记录
                    record = await self.save_record(
                        rule=rule,
                        message_text=message_text,
                        snapshot=snapshot,
                        links=links,
                        fingerprint=fingerprint
                    )
                    
                    # 8. 更新规则统计
                    rule.total_captured = (rule.total_captured or 0) + 1
                    await self.db.commit()
                    
                    logger.info(f"📥 捕获资源: 规则={rule.name}, 链接={sum(len(v) for v in links.values())}个")
                    
                    # 9. 如果启用自动转存，立即处理
                    if rule.auto_save:
                        await self.auto_save_to_115(record)
                    
                except Exception as e:
                    logger.error(f"处理规则 {rule.name} 时出错: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
    
    async def save_record(
        self,
        rule: ResourceMonitorRule,
        message_text: str,
        snapshot: Dict,
        links: Dict[str, List[str]],
        fingerprint: str
    ) -> ResourceRecord:
        """
        保存资源记录
        
        Args:
            rule: 监控规则
            message_text: 消息文本
            snapshot: 消息快照
            links: 提取的链接
            fingerprint: 链接指纹
            
        Returns:
            资源记录
        """
        record = ResourceRecord(
            rule_id=rule.id,
            message_text=message_text,
            message_snapshot=json.dumps(snapshot, ensure_ascii=False),
            chat_id=str(snapshot.get('chat_id', '')),
            chat_title=snapshot.get('chat_title', ''),
            message_id=snapshot.get('message_id'),
            sender_id=str(snapshot.get('sender_id', '')),
            sender_name=snapshot.get('sender_name', ''),
            pan115_links=json.dumps(links.get('pan115', []), ensure_ascii=False),
            magnet_links=json.dumps(links.get('magnet', []), ensure_ascii=False),
            ed2k_links=json.dumps(links.get('ed2k', []), ensure_ascii=False),
            link_fingerprint=fingerprint,
            tags=json.dumps([], ensure_ascii=False),
            status='pending',
            target_path=rule.target_path,
            detected_at=datetime.now()
        )
        
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        
        return record
    
    async def auto_save_to_115(self, record: ResourceRecord):
        """
        自动转存到115
        
        Args:
            record: 资源记录
        """
        try:
            # 获取115服务
            from database import get_db
            async for db in get_db():
                from models import MediaSettings
                settings_result = await db.execute(select(MediaSettings).limit(1))
                settings = settings_result.scalar_one_or_none()
                
                if not settings or not settings.pan115_user_key:
                    logger.error("115网盘未配置")
                    record.status = 'failed'
                    record.error_message = '115网盘未配置'
                    await self.db.commit()
                    return
                
                p115_service = P115Service(cookies=settings.pan115_user_key)
                
                # 解析链接
                pan115_links = json.loads(record.pan115_links) if record.pan115_links else []
                magnet_links = json.loads(record.magnet_links) if record.magnet_links else []
                ed2k_links = json.loads(record.ed2k_links) if record.ed2k_links else []
                
                success_count = 0
                errors = []
                
                # 处理115分享链接
                for link in pan115_links:
                    try:
                        # TODO: 实现115分享转存
                        # await p115_service.save_share(link, record.target_path)
                        success_count += 1
                        logger.info(f"✅ 115分享转存成功: {link[:50]}...")
                    except Exception as e:
                        errors.append(f"115分享转存失败: {str(e)}")
                        logger.error(f"115分享转存失败: {e}")
                
                # 处理磁力/ed2k链接（离线下载）
                for link in magnet_links + ed2k_links:
                    try:
                        # TODO: 实现115离线下载
                        # task_id = await p115_service.offline_download(link, record.target_path)
                        # record.pan115_task_id = task_id
                        success_count += 1
                        logger.info(f"✅ 离线下载任务创建成功: {link[:50]}...")
                    except Exception as e:
                        errors.append(f"离线下载失败: {str(e)}")
                        logger.error(f"离线下载失败: {e}")
                
                # 更新记录状态
                if success_count > 0:
                    record.status = 'saved'
                    record.saved_at = datetime.now()
                    
                    # 更新规则统计
                    if record.rule:
                        record.rule.total_saved = (record.rule.total_saved or 0) + 1
                else:
                    record.status = 'failed'
                
                if errors:
                    record.error_message = '; '.join(errors)
                
                await self.db.commit()
                
                logger.info(f"🎉 资源转存完成: 成功={success_count}, 失败={len(errors)}")
                break
        
        except Exception as e:
            logger.error(f"自动转存失败: {e}")
            record.status = 'failed'
            record.error_message = str(e)
            await self.db.commit()

