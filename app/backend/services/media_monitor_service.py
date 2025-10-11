"""
媒体监控服务
负责监听 Telegram 消息，下载符合规则的媒体文件
"""
import asyncio
import json
import hashlib
import shutil
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from log_manager import get_logger

logger = get_logger('media_monitor')
from database import get_db
from models import MediaMonitorRule, DownloadTask, MediaFile, MediaSettings
from utils.media_filters import MediaFilter
from utils.message_deduplicator import SenderFilter
from utils.media_metadata import MediaMetadataExtractor

# 导入 115网盘 Open API 客户端
try:
    from services.pan115_client import Pan115Client
    PAN115_AVAILABLE = True
except ImportError:
    PAN115_AVAILABLE = False
    logger.warning("115网盘客户端未安装，115直传功能将不可用")


class FileOrganizer:
    """文件归档管理器"""
    
    @staticmethod
    def generate_target_directory(rule: MediaMonitorRule, metadata: Dict[str, Any]) -> str:
        """
        生成目标文件夹路径
        
        Args:
            rule: 监控规则
            metadata: 元数据（包含发送者、来源等信息）
            
        Returns:
            相对路径字符串
        """
        from datetime import datetime
        
        if rule.folder_structure == 'flat':
            return ''
        
        elif rule.folder_structure == 'date':
            now = datetime.now()
            return f"{now.year}/{now.month:02d}/{now.day:02d}"
        
        elif rule.folder_structure == 'type':
            file_type = metadata.get('type', 'other')
            return file_type
        
        elif rule.folder_structure == 'source':
            source = metadata.get('source_chat', 'unknown')
            return FileOrganizer._sanitize_path(source)
        
        elif rule.folder_structure == 'sender':
            # 优先使用 sender_name（包含用户名或真实姓名），fallback 到 sender_username，最后是 sender_id
            sender = metadata.get('sender_name') or metadata.get('sender_username') or str(metadata.get('sender_id', 'unknown'))
            return FileOrganizer._sanitize_path(sender)
        
        elif rule.folder_structure == 'custom':
            template = rule.custom_folder_template or '{type}/{year}/{month}/{day}'
            now = datetime.now()
            
            replacements = {
                '{year}': str(now.year),
                '{month}': f"{now.month:02d}",
                '{day}': f"{now.day:02d}",
                '{type}': metadata.get('type', 'other'),
                '{source}': FileOrganizer._sanitize_path(metadata.get('source_chat', 'unknown')),
                '{source_id}': metadata.get('source_chat_id', 'unknown'),
                '{sender}': FileOrganizer._sanitize_path(
                    metadata.get('sender_name') or metadata.get('sender_username') or str(metadata.get('sender_id', 'unknown'))
                ),
                '{sender_id}': str(metadata.get('sender_id', 'unknown')),
            }
            
            path = template
            for key, value in replacements.items():
                path = path.replace(key, value)
            
            return path
        
        return ''
    
    @staticmethod
    def generate_filename(rule: MediaMonitorRule, original_name: str, metadata: Dict[str, Any]) -> str:
        """
        生成目标文件名
        
        Args:
            rule: 监控规则
            original_name: 原始文件名
            metadata: 元数据
            
        Returns:
            文件名字符串
        """
        if not rule.rename_files or not rule.filename_template:
            return original_name
        
        template = rule.filename_template
        now = datetime.now()
        
        # 分离扩展名
        name_without_ext = Path(original_name).stem
        extension = Path(original_name).suffix
        
        replacements = {
            '{date}': now.strftime('%Y%m%d'),
            '{time}': now.strftime('%H%M%S'),
            '{sender}': FileOrganizer._sanitize_filename(
                metadata.get('sender_name') or metadata.get('sender_username') or str(metadata.get('sender_id', 'unknown'))
            ),
            '{source}': FileOrganizer._sanitize_filename(metadata.get('source_chat', 'unknown')),
            '{type}': metadata.get('type', 'file'),
            '{original_name}': name_without_ext
        }
        
        filename = template
        for key, value in replacements.items():
            filename = filename.replace(key, str(value))
        
        return filename + extension
    
    @staticmethod
    async def organize_file(
        rule: MediaMonitorRule,
        temp_path: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        归档文件
        
        Args:
            rule: 监控规则
            temp_path: 临时文件路径
            metadata: 元数据
            
        Returns:
            归档后的文件路径，失败返回 None
        """
        try:
            if not rule.organize_enabled:
                return None
            
            # 生成目标路径
            target_dir_relative = FileOrganizer.generate_target_directory(rule, metadata)
            original_filename = Path(temp_path).name
            target_filename = FileOrganizer.generate_filename(rule, original_filename, metadata)
            
            # 根据归档目标类型确定基础路径
            base_path = Path(rule.organize_local_path or '/app/media/organized')
            
            # 完整目标路径
            target_dir = base_path / target_dir_relative
            target_dir.mkdir(parents=True, exist_ok=True)
            
            target_path = target_dir / target_filename
            
            # 如果文件已存在，添加序号
            counter = 1
            while target_path.exists():
                name_without_ext = Path(target_filename).stem
                extension = Path(target_filename).suffix
                target_path = target_dir / f"{name_without_ext}_{counter}{extension}"
                counter += 1
            
            # 执行归档
            if rule.organize_mode == 'move':
                shutil.move(temp_path, target_path)
                logger.info(f"📦 移动文件: {temp_path} -> {target_path}")
            else:  # copy
                shutil.copy2(temp_path, target_path)
                logger.info(f"📋 复制文件: {temp_path} -> {target_path}")
                
                # 如果不保留临时文件，删除它
                if not rule.keep_temp_file:
                    os.remove(temp_path)
                    logger.info(f"🗑️ 删除临时文件: {temp_path}")
            
            return str(target_path)
            
        except Exception as e:
            logger.error(f"文件归档失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def _sanitize_path(path: str) -> str:
        """清理路径字符串，移除非法字符"""
        # 移除路径中的非法字符
        illegal_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in illegal_chars:
            path = path.replace(char, '_')
        return path.strip()
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除文件名中的非法字符
        illegal_chars = ['/', '\\', '<', '>', ':', '"', '|', '?', '*']
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        return filename.strip()


class MediaMonitorService:
    """媒体监控服务"""
    
    def __init__(self):
        self.active_monitors: Dict[int, bool] = {}  # rule_id -> is_active
        self.download_queue = asyncio.Queue()
        self.download_workers: List[asyncio.Task] = []
        self.is_running = False
        self.global_settings: Optional[MediaSettings] = None
        
    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值（优先使用全局配置）"""
        if self.global_settings and hasattr(self.global_settings, key):
            value = getattr(self.global_settings, key)
            return value if value is not None else default
        return default
    
    async def _load_global_settings(self):
        """加载全局媒体配置"""
        try:
            async for db in get_db():
                result = await db.execute(select(MediaSettings))
                settings = result.scalars().first()
                
                if settings:
                    self.global_settings = settings
                    logger.info("✅ 已加载全局媒体配置")
                else:
                    # 创建默认配置
                    settings = MediaSettings(
                        temp_folder="/app/media/downloads",
                        concurrent_downloads=3,
                        retry_on_failure=True,
                        max_retries=3,
                        extract_metadata=True,
                        metadata_mode="lightweight",
                        metadata_timeout=10,
                        async_metadata_extraction=True,
                        auto_cleanup_enabled=True,
                        auto_cleanup_days=7,
                        cleanup_only_organized=True,
                        max_storage_gb=100
                    )
                    db.add(settings)
                    await db.commit()
                    await db.refresh(settings)
                    self.global_settings = settings
                    logger.info("📝 创建默认全局媒体配置")
                break
        except Exception as e:
            logger.error(f"加载全局配置失败: {e}")
            # 使用内存中的默认配置
            self.global_settings = None
    
    async def start(self):
        """启动监控服务"""
        if self.is_running:
            logger.warning("媒体监控服务已在运行")
            return
        
        self.is_running = True
        logger.info("🎬 启动媒体监控服务")
        
        # 重置所有"下载中"的任务状态（容器重启后这些任务已中断）
        await self._reset_downloading_tasks()
        
        # 加载全局配置
        await self._load_global_settings()
        
        # 启动下载工作线程
        await self._start_download_workers()
        
        # 加载并启动所有活跃的监控规则
        await self._load_active_rules()
    
    async def _reset_downloading_tasks(self):
        """重置所有"下载中"状态的任务（容器重启后需要调用）"""
        try:
            async for db in get_db():
                # 查找所有"下载中"、"等待中"或"失败"状态的任务（失败的也可以自动重试）
                result = await db.execute(
                    select(DownloadTask).where(
                        or_(
                            DownloadTask.status == 'downloading',
                            DownloadTask.status == 'pending',
                            DownloadTask.status == 'failed'
                        )
                    )
                )
                interrupted_tasks = result.scalars().all()
                
                if interrupted_tasks:
                    logger.info(f"🔄 发现 {len(interrupted_tasks)} 个中断的下载任务，准备自动续传")
                    
                    # 将任务按规则分组，准备重新加入队列
                    tasks_by_rule = {}
                    for task in interrupted_tasks:
                        if task.monitor_rule_id not in tasks_by_rule:
                            tasks_by_rule[task.monitor_rule_id] = []
                        tasks_by_rule[task.monitor_rule_id].append(task)
                    
                    # 对每个任务尝试自动续传
                    resumed_count = 0
                    failed_count = 0
                    
                    for rule_id, tasks in tasks_by_rule.items():
                        # 获取规则
                        rule_result = await db.execute(
                            select(MediaMonitorRule).where(MediaMonitorRule.id == rule_id)
                        )
                        rule = rule_result.scalar_one_or_none()
                        
                        if not rule:
                            logger.warning(f"规则不存在: {rule_id}，无法续传相关任务")
                            for task in tasks:
                                task.status = 'failed'
                                task.failed_at = datetime.now()
                                task.last_error = "关联的监控规则已删除"
                                failed_count += 1
                            continue
                        
                        # 为每个任务尝试续传
                        for task in tasks:
                            # 检查重试次数，避免无限重试
                            max_auto_retry = task.max_retries or 3
                            current_retry = task.retry_count or 0
                            
                            if current_retry >= max_auto_retry:
                                logger.warning(f"   - 跳过任务（已达最大重试次数 {max_auto_retry}）: {task.file_name} (ID: {task.id})")
                                task.status = 'failed'
                                task.last_error = f"已达最大重试次数（{max_auto_retry}次），请手动重试"
                                failed_count += 1
                                continue
                            
                            # 重置为pending状态，保留进度信息
                            old_status = task.status
                            task.status = 'pending'
                            task.retry_count = current_retry + 1
                            task.last_error = f"容器重启自动重试中... (第{task.retry_count}/{max_auto_retry}次)"
                            
                            logger.info(f"   - 准备续传: {task.file_name} (ID: {task.id}, 原状态: {old_status}, 重试: {task.retry_count}/{max_auto_retry})")
                            resumed_count += 1
                    
                    await db.commit()
                    
                    logger.info(f"✅ 任务重置完成: {resumed_count}个待续传, {failed_count}个失败")
                    logger.info(f"💡 提示: 系统将在5秒后自动尝试续传这些任务")
                    
                    # 延迟5秒后启动自动续传
                    import asyncio
                    asyncio.create_task(self._auto_resume_tasks(db))
                else:
                    logger.info("✅ 没有需要重置的下载任务")
                
                break  # 只需要执行一次
        except Exception as e:
            logger.error(f"重置下载任务失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def _auto_resume_tasks(self, db: AsyncSession):
        """自动续传中断的任务"""
        try:
            # 等待5秒，确保所有服务都已启动
            await asyncio.sleep(5)
            
            logger.info("🚀 开始自动续传中断的下载任务...")
            
            # 查找所有pending状态的任务
            result = await db.execute(
                select(DownloadTask).where(DownloadTask.status == 'pending')
            )
            pending_tasks = result.scalars().all()
            
            if not pending_tasks:
                logger.info("没有待续传的任务")
                return
            
            # 获取enhanced_bot实例
            from main import get_enhanced_bot
            enhanced_bot = get_enhanced_bot()
            if not enhanced_bot:
                logger.error("无法获取enhanced_bot实例，续传失败")
                return
            
            # 为每个任务重新获取消息并加入队列
            resumed = 0
            failed = 0
            
            for task in pending_tasks:
                try:
                    # 查找可用的客户端
                    client_wrapper = None
                    client = None
                    
                    for client_manager in enhanced_bot.multi_client_manager.clients.values():
                        if client_manager.is_authorized and client_manager.loop and client_manager.client:
                            client_wrapper = client_manager
                            client = client_manager.client
                            break
                    
                    if not client or not client_wrapper:
                        raise Exception("没有可用的Telegram客户端")
                    
                    # 重新获取消息
                    if not task.chat_id or not task.message_id:
                        raise Exception("任务缺少chat_id或message_id")
                    
                    future = asyncio.run_coroutine_threadsafe(
                        client.get_messages(int(task.chat_id), message_ids=task.message_id),
                        client_wrapper.loop
                    )
                    message = future.result(timeout=10)
                    
                    if not message:
                        raise Exception("无法获取原始消息")
                    
                    # 加入下载队列
                    await self.download_queue.put({
                        'task_id': task.id,
                        'rule_id': task.monitor_rule_id,
                        'message_id': task.message_id,
                        'chat_id': int(task.chat_id),
                        'file_name': task.file_name,
                        'file_type': task.file_type,
                        'client': client,
                        'message': message,
                        'client_wrapper': client_wrapper
                    })
                    
                    logger.info(f"✅ 续传任务已加入队列: {task.file_name}")
                    resumed += 1
                    
                except Exception as e:
                    logger.error(f"❌ 续传任务失败 {task.file_name}: {e}")
                    task.status = 'failed'
                    task.failed_at = datetime.now()
                    task.last_error = f"自动续传失败: {str(e)}"
                    failed += 1
            
            await db.commit()
            logger.info(f"🎉 自动续传完成: {resumed}个成功, {failed}个失败")
            
        except Exception as e:
            logger.error(f"自动续传任务异常: {e}")
            import traceback
            traceback.print_exc()
    
    async def stop(self):
        """停止监控服务"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("🛑 停止媒体监控服务")
        
        # 停止所有下载工作线程
        for worker in self.download_workers:
            worker.cancel()
        
        self.download_workers.clear()
        self.active_monitors.clear()
    
    async def _load_active_rules(self):
        """加载所有活跃的监控规则"""
        try:
            async for db in get_db():
                result = await db.execute(
                    select(MediaMonitorRule).where(MediaMonitorRule.is_active == True)
                )
                active_rules = result.scalars().all()
                
                for rule in active_rules:
                    self.active_monitors[rule.id] = True
                    logger.info(f"✅ 加载监控规则: {rule.name} (ID: {rule.id})")
                
                logger.info(f"📊 已加载 {len(active_rules)} 个活跃监控规则")
                break
                
        except Exception as e:
            logger.error(f"加载监控规则失败: {e}")
    
    async def _start_download_workers(self, worker_count: int = 5):
        """启动下载工作线程（增加并发提升速度）"""
        for i in range(worker_count):
            worker = asyncio.create_task(self._download_worker(i))
            self.download_workers.append(worker)
            logger.info(f"🔧 启动下载工作线程 #{i+1}")
    
    async def _download_worker(self, worker_id: int):
        """下载工作线程"""
        logger.info(f"👷 下载工作线程 #{worker_id+1} 已启动")
        
        while self.is_running:
            try:
                # 从队列获取下载任务
                task = await asyncio.wait_for(
                    self.download_queue.get(),
                    timeout=1.0
                )
                
                logger.info(f"[Worker #{worker_id+1}] 开始下载: {task['file_name']}")
                
                # 执行下载
                await self._execute_download(task)
                
                # 标记任务完成
                self.download_queue.task_done()
                
            except asyncio.TimeoutError:
                # 队列为空，继续等待
                continue
            except Exception as e:
                logger.error(f"[Worker #{worker_id+1}] 下载任务失败: {e}")
    
    async def process_message(self, client, message, rule_id: int, client_wrapper=None):
        """
        处理接收到的消息
        
        Args:
            client: Telegram 客户端
            message: 消息对象
            rule_id: 监控规则ID
            client_wrapper: 客户端包装器（用于访问事件循环）
        """
        try:
            logger.info(f"🔍 处理媒体消息: rule_id={rule_id}, message_id={message.id}")
            logger.info(f"📊 当前活跃监控规则: {list(self.active_monitors.keys())}")
            
            # 检查规则是否活跃
            if rule_id not in self.active_monitors:
                logger.warning(f"⚠️ 规则 {rule_id} 不在活跃监控列表中，跳过处理")
                return
            
            # 获取规则配置
            async for db in get_db():
                result = await db.execute(
                    select(MediaMonitorRule).where(MediaMonitorRule.id == rule_id)
                )
                rule = result.scalar_one_or_none()
                
                if not rule or not rule.is_active:
                    logger.warning(f"⚠️ 规则 {rule_id} 未找到或未激活")
                    return
                
                # 检查消息是否包含媒体
                if not self._has_media(message):
                    logger.info(f"⏭️ 消息 {message.id} 不包含媒体，跳过")
                    return
                
                logger.info(f"✅ 消息 {message.id} 包含媒体，应用过滤器")
                
                # 应用过滤器
                if not await self._apply_filters(message, rule):
                    logger.info(f"⏭️ 消息 {message.id} 未通过过滤器")
                    return
                
                logger.info(f"✅ 消息 {message.id} 通过所有过滤器，创建下载任务")
                
                # 创建下载任务（传递client_wrapper）
                await self._create_download_task(db, message, rule, client, client_wrapper)
                
                break
                
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _has_media(self, message) -> bool:
        """检查消息是否包含媒体"""
        return bool(
            message.photo or
            message.video or
            message.audio or
            message.voice or
            message.document
        )
    
    async def _apply_filters(self, message, rule: MediaMonitorRule) -> bool:
        """
        应用所有过滤器
        
        Returns:
            是否通过所有过滤器
        """
        try:
            # 1. 文件类型过滤
            if rule.media_types:
                media_types_raw = rule.media_types
                # 如果已经是列表，直接使用；否则解析JSON
                if isinstance(media_types_raw, str):
                    allowed_types = json.loads(media_types_raw)
                    # 如果解析结果仍是字符串（双重编码），再解析一次
                    if isinstance(allowed_types, str):
                        allowed_types = json.loads(allowed_types)
                else:
                    allowed_types = media_types_raw
                
                if not MediaFilter.check_file_type(message, allowed_types):
                    logger.info(f"⏭️ 文件类型不匹配，跳过。允许的类型: {allowed_types}")
                    return False
            
            # 2. 文件大小过滤
            if not MediaFilter.check_file_size(message, rule.min_size_mb or 0, rule.max_size_mb or 2000):
                logger.info(f"⏭️ 文件大小不符合要求，跳过。范围: {rule.min_size_mb}-{rule.max_size_mb} MB")
                return False
            
            # 3. 文件名过滤
            if not MediaFilter.check_filename(message, rule.filename_include, rule.filename_exclude):
                logger.info(f"⏭️ 文件名不匹配，跳过。包含: {rule.filename_include}, 排除: {rule.filename_exclude}")
                return False
            
            # 4. 文件扩展名过滤
            if rule.file_extensions:
                extensions_raw = rule.file_extensions
                # 如果已经是列表，直接使用；否则解析JSON
                if isinstance(extensions_raw, str):
                    allowed_extensions = json.loads(extensions_raw)
                    # 如果解析结果仍是字符串（双重编码），再解析一次
                    if isinstance(allowed_extensions, str):
                        allowed_extensions = json.loads(allowed_extensions)
                else:
                    allowed_extensions = extensions_raw
                
                if allowed_extensions and not MediaFilter.check_file_extension(message, allowed_extensions):
                    logger.info(f"⏭️ 文件扩展名不匹配，跳过。允许的扩展名: {allowed_extensions}")
                    return False
            
            # 5. 发送者过滤
            if rule.enable_sender_filter:
                sender_info = SenderFilter.get_sender_info(message)
                is_allowed = SenderFilter.is_sender_allowed(
                    sender_info['id'],
                    sender_info['username'],
                    rule.sender_filter_mode or 'whitelist',
                    rule.sender_whitelist,
                    rule.sender_blacklist
                )
                
                if not is_allowed:
                    logger.info(f"⏭️ 发送者被过滤，跳过: {sender_info['username'] or sender_info['id']}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"应用过滤器失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _create_download_task(
        self,
        db: AsyncSession,
        message,
        rule: MediaMonitorRule,
        client,
        client_wrapper=None
    ):
        """创建下载任务"""
        try:
            # 获取媒体信息
            media_info = MediaFilter.get_media_info(message)
            
            # 生成文件名（确保有扩展名）
            if media_info['filename']:
                filename = media_info['filename']
            else:
                # 根据媒体类型生成默认文件名
                ext = media_info['extension'] or ''
                if not ext and media_info['type']:
                    # 如果没有扩展名，根据类型推断
                    type_ext_map = {
                        'photo': '.jpg',
                        'video': '.mp4',
                        'document': '.file',
                        'audio': '.mp3',
                        'voice': '.ogg',
                        'sticker': '.webp'
                    }
                    ext = type_ext_map.get(media_info['type'], '.file')
                filename = f"{media_info['type']}_{message.id}{ext}"
            
            # 提取文件元数据（用于重新下载）
            file_unique_id = None
            file_access_hash = None
            media_json = None
            
            try:
                import json
                if hasattr(message, 'media') and message.media:
                    # 获取文件的唯一ID和访问哈希
                    if hasattr(message.media, 'document'):
                        doc = message.media.document
                        if hasattr(doc, 'id'):
                            file_unique_id = str(doc.id)
                        if hasattr(doc, 'access_hash'):
                            file_access_hash = str(doc.access_hash)
                    elif hasattr(message.media, 'photo'):
                        photo = message.media.photo
                        if hasattr(photo, 'id'):
                            file_unique_id = str(photo.id)
                        if hasattr(photo, 'access_hash'):
                            file_access_hash = str(photo.access_hash)
                    
                    # 保存媒体信息JSON（用于恢复）
                    media_dict = {
                        'type': media_info['type'],
                        'filename': filename,
                        'size': media_info['size'],
                        'mime_type': media_info.get('mime_type')
                    }
                    media_json = json.dumps(media_dict, ensure_ascii=False)
            except Exception as e:
                logger.warning(f"提取文件元数据失败: {e}")
            
            # 创建下载任务记录
            task = DownloadTask(
                monitor_rule_id=rule.id,
                message_id=message.id,
                chat_id=str(message.chat_id) if hasattr(message, 'chat_id') else None,
                file_name=filename,
                file_type=media_info['type'],
                file_size_mb=media_info['size_mb'],
                file_unique_id=file_unique_id,
                file_access_hash=file_access_hash,
                media_json=media_json,
                status='pending',
                priority=0,
                total_bytes=media_info['size'],
                max_retries=self._get_config_value('max_retries', 3)
            )
            
            db.add(task)
            await db.commit()
            
            # 刷新任务对象以获取数据库生成的ID
            try:
                await db.refresh(task)
            except Exception as refresh_error:
                # 如果刷新失败，尝试重新查询获取ID
                logger.warning(f"⚠️ 刷新任务失败，尝试重新查询: {refresh_error}")
                result = await db.execute(
                    select(DownloadTask).where(
                        DownloadTask.file_unique_id == file_unique_id,
                        DownloadTask.monitor_rule_id == rule.id
                    ).order_by(DownloadTask.id.desc())
                )
                task = result.scalar_one_or_none()
                if not task:
                    raise Exception("无法获取创建的下载任务")
            
            logger.info(f"📥 创建下载任务: {filename} (ID: {task.id})")
            
            # 添加到下载队列（包含client_wrapper）
            await self.download_queue.put({
                'task_id': task.id,
                'rule_id': rule.id,
                'message_id': message.id,
                'chat_id': message.chat_id if hasattr(message, 'chat_id') else None,
                'file_name': filename,
                'file_type': media_info['type'],
                'client': client,
                'message': message,
                'client_wrapper': client_wrapper  # 传递客户端包装器
            })
            
        except Exception as e:
            logger.error(f"创建下载任务失败: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
    
    async def _execute_download(self, task_data: Dict[str, Any]):
        """执行下载任务"""
        task_id = task_data['task_id']
        
        try:
            async for db in get_db():
                # 获取任务和规则
                result = await db.execute(
                    select(DownloadTask).where(DownloadTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                
                if not task:
                    logger.warning(f"下载任务不存在: {task_id}")
                    return
                
                result = await db.execute(
                    select(MediaMonitorRule).where(MediaMonitorRule.id == task.monitor_rule_id)
                )
                rule = result.scalar_one_or_none()
                
                if not rule:
                    logger.warning(f"监控规则不存在: {task.monitor_rule_id}")
                    return
                
                # 更新任务状态
                task.status = 'downloading'
                task.started_at = datetime.now()
                await db.commit()
                
                # 确保下载目录存在
                download_dir = Path(rule.temp_folder or '/app/media/downloads')
                download_dir.mkdir(parents=True, exist_ok=True)
                
                # 下载文件
                file_path = download_dir / task.file_name
                
                # 提前获取客户端、消息和包装器（避免作用域问题）
                client = task_data.get('client')
                message = task_data.get('message')
                client_wrapper = task_data.get('client_wrapper')
                
                # 检查是否存在不完整的文件，如果存在则删除（Pyrogram不支持真正的断点续传）
                skip_download = False
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    expected_size = task.total_bytes or 0
                    if file_size < expected_size:
                        logger.warning(f"🗑️ 发现不完整的文件 {task.file_name} ({file_size}/{expected_size} bytes)，删除重新下载")
                        file_path.unlink()
                    elif file_size == expected_size:
                        logger.info(f"✅ 文件已存在且完整: {task.file_name}，跳过下载直接整理")
                        skip_download = True
                        # 更新下载进度
                        task.downloaded_bytes = expected_size
                        task.progress_percent = 100
                        await db.commit()
                
                if not skip_download:
                    logger.info(f"⬇️ 开始下载: {task.file_name} -> {file_path}")
                    
                    # 验证客户端和消息对象
                    if not client or not message:
                        raise Exception("缺少客户端或消息对象")
                    
                    # 检查消息是否包含媒体
                    logger.info(f"📋 消息信息: ID={message.id if hasattr(message, 'id') else 'N/A'}, "
                               f"has_media={hasattr(message, 'media') and message.media is not None}, "
                               f"media_type={type(message.media).__name__ if hasattr(message, 'media') and message.media else 'None'}")
                    
                    if not hasattr(message, 'media') or message.media is None:
                        raise Exception(f"消息不包含媒体文件，可能已被删除。请删除此任务。")
                    
                    # 使用客户端包装器的事件循环下载（避免事件循环冲突）
                    if client_wrapper and hasattr(client_wrapper, 'loop') and client_wrapper.loop:
                        # 在客户端的事件循环中执行下载
                        import asyncio
                        from concurrent.futures import TimeoutError as FutureTimeoutError
                        
                        # 定义进度回调函数
                        last_progress_log = [0]  # 使用列表以便在闭包中修改
                        last_db_update = [0]  # 上次更新数据库的时间
                        
                        def progress_callback(current, total):
                            percent = (current / total * 100) if total > 0 else 0
                            current_mb = current / 1024 / 1024
                            total_mb = total / 1024 / 1024
                            
                            # 每5%记录一次日志（大文件也能及时看到进度）
                            progress_step = int(percent / 5)
                            if progress_step > last_progress_log[0]:
                                last_progress_log[0] = progress_step
                                logger.info(f"📥 下载进度: {task.file_name} - {percent:.1f}% ({current_mb:.1f}MB/{total_mb:.1f}MB)")
                            
                            # 每2秒更新一次数据库（给前端实时进度）
                            import time
                            current_time = time.time()
                            if current_time - last_db_update[0] >= 2.0:
                                last_db_update[0] = current_time
                                # 异步更新数据库
                                asyncio.create_task(self._update_task_progress(task.id, percent, current, total))
                        
                        # 下载重试逻辑（处理代理连接失败）
                        download_max_retries = 3
                        download_success = False
                        
                        for download_retry in range(download_max_retries):
                            try:
                                if download_retry > 0:
                                    logger.warning(f"🔄 下载重试 {download_retry}/{download_max_retries-1}: {task.file_name}")
                                    # 删除不完整的文件
                                    if file_path.exists():
                                        os.remove(file_path)
                                    # 等待5秒让代理恢复（使用异步sleep）
                                    await asyncio.sleep(5)
                                
                                # 使用异步Future，避免阻塞
                                # Telethon API: download_media(message, file=path, progress_callback=callback)
                                future = asyncio.run_coroutine_threadsafe(
                                    client.download_media(
                                        message, 
                                        file=str(file_path),
                                        progress_callback=progress_callback
                                    ),
                                    client_wrapper.loop
                                )
                                
                                # 异步等待，不阻塞事件循环（超时2小时，适合GB级大视频）
                                loop = asyncio.get_event_loop()
                                result = await asyncio.wait_for(
                                    asyncio.wrap_future(future),
                                    timeout=7200
                                )
                                logger.info(f"📦 download_media 返回值: {result}, 类型: {type(result)}")
                                download_success = True
                                break
                                
                            except (asyncio.TimeoutError, Exception) as download_error:
                                error_msg = str(download_error)
                                if download_retry < download_max_retries - 1:
                                    logger.warning(f"⚠️ 下载失败: {error_msg[:100]}, 准备重试...")
                                else:
                                    logger.error(f"❌ 下载失败（已重试{download_max_retries}次）: {error_msg[:200]}")
                                    raise Exception(f"下载失败（已重试{download_max_retries}次）: {error_msg[:100]}")
                        
                        if not download_success:
                            raise Exception("下载失败，所有重试均失败")
                    else:
                        # 降级方案：直接下载（可能失败）
                        await client.download_media(message, file=str(file_path))
                    
                    logger.info(f"✅ 下载完成: {task.file_name}")
                
                # 验证文件是否成功下载
                if not file_path.exists():
                    raise Exception("文件下载失败，文件不存在")
                
                # 计算文件哈希
                file_hash = await self._calculate_file_hash(str(file_path))
                
                # 检查是否已存在相同哈希的文件（去重）
                result = await db.execute(
                    select(MediaFile).where(MediaFile.file_hash == file_hash)
                )
                existing_file = result.scalar_one_or_none()
                
                if existing_file:
                    logger.info(f"⏭️ 文件已存在（哈希相同），跳过: {task.file_name}")
                    # 删除刚下载的重复文件
                    os.remove(file_path)
                    
                    # 更新任务状态为成功但跳过
                    task.status = 'success'
                    task.completed_at = datetime.now()
                    task.progress_percent = 100
                    task.last_error = "文件已存在（重复）"
                    await db.commit()
                    
                    break
                
                # 提取元数据（使用全局配置）
                metadata_dict = {}
                extract_metadata = self._get_config_value('extract_metadata', True)
                metadata_mode = self._get_config_value('metadata_mode', 'lightweight')
                
                if extract_metadata and metadata_mode != 'disabled':
                    try:
                        async_extraction = self._get_config_value('async_metadata_extraction', True)
                        timeout = self._get_config_value('metadata_timeout', 10)
                        
                        if async_extraction:
                            # 异步提取，不阻塞
                            metadata_dict = await MediaMetadataExtractor.extract_metadata_async(
                                str(file_path),
                                mode=metadata_mode,
                                timeout=timeout
                            )
                        else:
                            # 同步提取
                            metadata_dict = await MediaMetadataExtractor.extract_metadata_async(
                                str(file_path),
                                mode=metadata_mode,
                                timeout=timeout
                            )
                        
                        logger.info(f"📊 元数据提取完成: {metadata_dict.get('type', 'unknown')}")
                    except Exception as meta_error:
                        logger.warning(f"元数据提取失败: {meta_error}")
                        metadata_dict = {'error': str(meta_error)}
                
                # 获取发送者和来源信息
                sender_info = SenderFilter.get_sender_info(message)
                
                # 获取聊天名称（优先从message对象）
                chat_name = 'unknown'
                if hasattr(message, 'chat') and message.chat:
                    chat = message.chat
                    # 尝试获取聊天标题或用户名
                    if hasattr(chat, 'title') and chat.title:
                        chat_name = chat.title
                    elif hasattr(chat, 'username') and chat.username:
                        chat_name = chat.username
                    elif hasattr(chat, 'first_name'):
                        chat_name = chat.first_name
                        if hasattr(chat, 'last_name') and chat.last_name:
                            chat_name += f" {chat.last_name}"
                
                logger.info(f"📝 聊天名称: {chat_name}, 聊天ID: {task.chat_id}")
                
                # 准备归档元数据
                # 构建发送者显示名称（优先级：username > 姓名 > ID）
                sender_display = sender_info.get('username')
                if not sender_display:
                    # 构建全名（只包含非空部分）
                    name_parts = []
                    if sender_info.get('first_name'):
                        name_parts.append(sender_info['first_name'])
                    if sender_info.get('last_name'):
                        name_parts.append(sender_info['last_name'])
                    sender_display = ' '.join(name_parts) if name_parts else None
                if not sender_display:
                    sender_display = str(sender_info.get('id', 'unknown'))
                
                logger.info(f"👤 发送者显示名称: {sender_display}, 发送者ID: {sender_info.get('id')}")
                
                organize_metadata = {
                    'type': task.file_type,
                    'sender_id': sender_info['id'],
                    'sender_username': sender_info.get('username'),
                    'sender_name': sender_display,  # 新增：发送者显示名称
                    'source_chat': chat_name,
                    'source_chat_id': str(task.chat_id) if task.chat_id else 'unknown'
                }
                
                # 初始化归档相关变量
                final_path = None
                pan115_path = None
                is_uploaded = False
                organize_failed = False
                organize_error = None
                
                # 检查归档目标类型
                should_upload_to_115 = rule.organize_enabled and rule.organize_target_type == 'pan115'
                should_organize_local = rule.organize_enabled and rule.organize_target_type != 'pan115'
                
                # 本地归档（仅当目标不是115网盘时）
                if should_organize_local:
                    try:
                        final_path = await FileOrganizer.organize_file(
                            rule,
                            str(file_path),
                            organize_metadata
                        )
                        
                        if final_path:
                            logger.info(f"📦 文件已归档到本地: {final_path}")
                    except Exception as e:
                        logger.error(f"❌ 本地归档失败: {e}")
                        organize_failed = True
                        organize_error = f"本地归档失败: {str(e)}"
                
                # 上传到115网盘（作为归档方式）
                elif should_upload_to_115:
                    try:
                        # 获取115网盘配置
                        pan115_user_key = self._get_config_value('pan115_user_key')
                        pan115_remote_base = rule.pan115_remote_path or self._get_config_value('pan115_remote_path', '/Telegram媒体')
                        
                        if not pan115_user_key:
                            error_msg = "115网盘未配置，请先在设置页面扫码登录115网盘"
                            logger.warning(f"⚠️ {error_msg}")
                            organize_failed = True
                            organize_error = error_msg
                        else:
                            logger.info(f"📤 115网盘归档模式")
                            
                            # 生成远程路径
                            remote_dir = FileOrganizer.generate_target_directory(rule, organize_metadata)
                            remote_filename = FileOrganizer.generate_filename(rule, task.file_name, organize_metadata)
                            
                            # 完整的115网盘目标路径
                            remote_target_dir = os.path.join(pan115_remote_base, remote_dir).replace('\\', '/')
                            pan115_path = os.path.join(remote_target_dir, remote_filename).replace('\\', '/')
                            
                            # 源文件（直接使用临时下载文件）
                            source_file = str(file_path)
                            
                            logger.info(f"📤 准备上传到115网盘: {remote_filename}")
                            logger.info(f"   本地文件: {source_file}")
                            logger.info(f"   目标路径: {pan115_path}")
                            
                            # 使用P115Service上传
                            from services.p115_service import P115Service
                            p115 = P115Service()
                            
                            upload_result = await p115.upload_file(
                                cookies=pan115_user_key,
                                file_path=source_file,
                                target_dir=remote_target_dir,
                                file_name=remote_filename
                            )
                            
                            if upload_result.get('success'):
                                is_uploaded = True
                                pan115_path = pan115_path  # 记录115网盘路径
                                logger.info(f"✅ 文件已上传到115网盘: {pan115_path}")
                                if upload_result.get('pickcode'):
                                    logger.info(f"📝 文件ID: {upload_result['pickcode']}")
                                if upload_result.get('is_quick'):
                                    logger.info("⚡ 秒传成功（文件已存在）")
                            else:
                                error_msg = upload_result.get('message', '未知错误')
                                logger.warning(f"⚠️ 115网盘上传失败: {error_msg}")
                                organize_failed = True
                                organize_error = f"115网盘上传失败: {error_msg}"
                    
                    except Exception as pan115_error:
                        error_msg = str(pan115_error)
                        logger.error(f"❌ 115网盘上传异常: {error_msg}")
                        organize_failed = True
                        organize_error = f"115网盘上传异常: {error_msg}"
                        import traceback
                        traceback.print_exc()
                
                # 创建媒体文件记录
                media_file = MediaFile(
                    monitor_rule_id=rule.id,
                    download_task_id=task.id,
                    message_id=message.id,
                    temp_path=str(file_path) if not final_path else None,
                    final_path=final_path,
                    pan115_path=pan115_path,
                    file_hash=file_hash,
                    file_name=task.file_name,
                    file_type=task.file_type,
                    file_size_mb=task.file_size_mb,
                    extension=Path(task.file_name).suffix,
                    original_name=task.file_name,
                    file_metadata=json.dumps(metadata_dict) if metadata_dict else None,
                    width=metadata_dict.get('width'),
                    height=metadata_dict.get('height'),
                    duration_seconds=int(metadata_dict.get('duration_seconds', 0)) if metadata_dict.get('duration_seconds') else None,
                    resolution=metadata_dict.get('resolution'),
                    codec=metadata_dict.get('codec'),
                    bitrate_kbps=metadata_dict.get('bitrate_kbps'),
                    source_chat=chat_name,  # 使用聊天名称而不是ID
                    sender_id=str(sender_info['id']),
                    sender_username=sender_display,  # 使用显示名称（username或姓名）
                    is_organized=(bool(final_path) or is_uploaded) and not organize_failed,  # 归档成功且未失败
                    is_uploaded_to_cloud=is_uploaded,
                    organize_failed=organize_failed,
                    organize_error=organize_error,
                    organized_at=datetime.now() if (final_path or is_uploaded) and not organize_failed else None,
                    uploaded_at=datetime.now() if is_uploaded else None
                )
                
                db.add(media_file)
                
                # 更新任务状态
                # 下载成功就标记为success，归档失败只影响媒体文件记录，不影响下载任务状态
                task.status = 'success'
                task.completed_at = datetime.now()
                task.progress_percent = 100
                
                # 更新规则统计
                rule.total_downloaded = (rule.total_downloaded or 0) + 1
                rule.total_size_mb = (rule.total_size_mb or 0) + task.file_size_mb
                rule.last_download_at = datetime.now()
                
                if organize_failed:
                    logger.warning(f"⚠️ 下载成功但归档失败: {task.file_name} - {organize_error}")
                else:
                    logger.info(f"🎉 下载任务完成: {task.file_name}")
                
                await db.commit()
                
                break
                
        except Exception as e:
            logger.error(f"下载任务执行失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 更新任务状态为失败
            try:
                async for db in get_db():
                    result = await db.execute(
                        select(DownloadTask).where(DownloadTask.id == task_id)
                    )
                    task = result.scalar_one_or_none()
                    
                    if task:
                        task.status = 'failed'
                        task.failed_at = datetime.now()
                        task.last_error = str(e)
                        task.retry_count = (task.retry_count or 0) + 1
                        
                        # 如果还可以重试，重新加入队列
                        if task.retry_count < task.max_retries:
                            task.status = 'pending'
                            await self.download_queue.put(task_data)
                            logger.info(f"🔄 重试下载任务: {task.file_name} ({task.retry_count}/{task.max_retries})")
                        else:
                            # 更新规则失败统计
                            result = await db.execute(
                                select(MediaMonitorRule).where(MediaMonitorRule.id == task.monitor_rule_id)
                            )
                            rule = result.scalar_one_or_none()
                            if rule:
                                rule.failed_downloads = (rule.failed_downloads or 0) + 1
                        
                        await db.commit()
                    
                    break
            except Exception as update_error:
                logger.error(f"更新任务状态失败: {update_error}")
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件的 SHA-256 哈希值"""
        try:
            sha256 = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {e}")
            return ""
    
    async def _update_task_progress(self, task_id: int, percent: float, current_bytes: int, total_bytes: int):
        """更新任务下载进度到数据库（给前端实时显示）"""
        try:
            async for db in get_db():
                result = await db.execute(
                    select(DownloadTask).where(DownloadTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                
                if task:
                    task.progress_percent = int(percent)
                    task.downloaded_bytes = current_bytes
                    task.total_bytes = total_bytes
                    await db.commit()
                
                break
        except Exception as e:
            # 进度更新失败不影响下载，只记录警告
            logger.debug(f"更新任务进度失败: {e}")
    
    async def reload_rule(self, rule_id: int):
        """重新加载单个监控规则"""
        try:
            async for db in get_db():
                result = await db.execute(
                    select(MediaMonitorRule).where(MediaMonitorRule.id == rule_id)
                )
                rule = result.scalar_one_or_none()
                
                if rule and rule.is_active:
                    self.active_monitors[rule_id] = True
                    logger.info(f"✅ 重新加载监控规则: {rule.name} (ID: {rule.id})")
                elif rule_id in self.active_monitors:
                    del self.active_monitors[rule_id]
                    logger.info(f"⏸️ 停用监控规则: ID {rule_id}")
                
                break
                
        except Exception as e:
            logger.error(f"重新加载监控规则失败: {e}")


# 全局媒体监控服务实例
_media_monitor_service: Optional[MediaMonitorService] = None


def get_media_monitor_service() -> MediaMonitorService:
    """获取媒体监控服务单例"""
    global _media_monitor_service
    
    if _media_monitor_service is None:
        _media_monitor_service = MediaMonitorService()
    
    return _media_monitor_service

