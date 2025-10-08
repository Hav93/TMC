"""
媒体监控服务
负责监听 Telegram 消息，下载符合规则的媒体文件
"""
import asyncio
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from database import get_db
from models import MediaMonitorRule, DownloadTask, MediaFile
from utils.media_filters import MediaFilter, SenderFilter
from utils.media_metadata import MediaMetadataExtractor


class MediaMonitorService:
    """媒体监控服务"""
    
    def __init__(self):
        self.active_monitors: Dict[int, bool] = {}  # rule_id -> is_active
        self.download_queue = asyncio.Queue()
        self.download_workers: List[asyncio.Task] = []
        self.is_running = False
        
    async def start(self):
        """启动监控服务"""
        if self.is_running:
            logger.warning("媒体监控服务已在运行")
            return
        
        self.is_running = True
        logger.info("🎬 启动媒体监控服务")
        
        # 启动下载工作线程
        await self._start_download_workers()
        
        # 加载并启动所有活跃的监控规则
        await self._load_active_rules()
    
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
    
    async def _start_download_workers(self, worker_count: int = 3):
        """启动下载工作线程"""
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
    
    async def process_message(self, client, message, rule_id: int):
        """
        处理接收到的消息
        
        Args:
            client: Telegram 客户端
            message: 消息对象
            rule_id: 监控规则ID
        """
        try:
            # 检查规则是否活跃
            if rule_id not in self.active_monitors:
                return
            
            # 获取规则配置
            async for db in get_db():
                result = await db.execute(
                    select(MediaMonitorRule).where(MediaMonitorRule.id == rule_id)
                )
                rule = result.scalar_one_or_none()
                
                if not rule or not rule.is_active:
                    return
                
                # 检查消息是否包含媒体
                if not self._has_media(message):
                    return
                
                # 应用过滤器
                if not await self._apply_filters(message, rule):
                    return
                
                # 创建下载任务
                await self._create_download_task(db, message, rule, client)
                
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
                allowed_types = json.loads(rule.media_types)
                if not MediaFilter.check_file_type(message, allowed_types):
                    logger.debug(f"⏭️ 文件类型不匹配，跳过")
                    return False
            
            # 2. 文件大小过滤
            if not MediaFilter.check_file_size(message, rule.min_size_mb or 0, rule.max_size_mb or 2000):
                logger.debug(f"⏭️ 文件大小不符合要求，跳过")
                return False
            
            # 3. 文件名过滤
            if not MediaFilter.check_filename(message, rule.filename_include, rule.filename_exclude):
                logger.debug(f"⏭️ 文件名不匹配，跳过")
                return False
            
            # 4. 文件扩展名过滤
            if rule.file_extensions:
                allowed_extensions = json.loads(rule.file_extensions)
                if not MediaFilter.check_file_extension(message, allowed_extensions):
                    logger.debug(f"⏭️ 文件扩展名不匹配，跳过")
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
                    logger.debug(f"⏭️ 发送者被过滤，跳过: {sender_info['username'] or sender_info['id']}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"应用过滤器失败: {e}")
            return False
    
    async def _create_download_task(
        self,
        db: AsyncSession,
        message,
        rule: MediaMonitorRule,
        client
    ):
        """创建下载任务"""
        try:
            # 获取媒体信息
            media_info = MediaFilter.get_media_info(message)
            
            # 生成文件名
            filename = media_info['filename'] or f"file_{message.id}{media_info['extension'] or ''}"
            
            # 创建下载任务记录
            task = DownloadTask(
                monitor_rule_id=rule.id,
                message_id=message.id,
                chat_id=str(message.chat_id) if hasattr(message, 'chat_id') else None,
                file_name=filename,
                file_type=media_info['type'],
                file_size_mb=media_info['size_mb'],
                status='pending',
                priority=0,
                total_bytes=media_info['size'],
                max_retries=rule.max_retries or 3
            )
            
            db.add(task)
            await db.commit()
            await db.refresh(task)
            
            logger.info(f"📥 创建下载任务: {filename} (ID: {task.id})")
            
            # 添加到下载队列
            await self.download_queue.put({
                'task_id': task.id,
                'rule_id': rule.id,
                'message_id': message.id,
                'chat_id': message.chat_id if hasattr(message, 'chat_id') else None,
                'file_name': filename,
                'file_type': media_info['type'],
                'client': client,
                'message': message
            })
            
        except Exception as e:
            logger.error(f"创建下载任务失败: {e}")
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
                
                logger.info(f"⬇️ 开始下载: {task.file_name} -> {file_path}")
                
                # 这里需要实际的下载逻辑（使用 Telegram 客户端）
                # 由于我们还没有集成到 enhanced_bot，这里先记录占位
                # TODO: 实现实际的文件下载
                client = task_data.get('client')
                message = task_data.get('message')
                
                if client and message:
                    await client.download_media(message, file=str(file_path))
                    logger.info(f"✅ 下载完成: {task.file_name}")
                else:
                    raise Exception("缺少客户端或消息对象")
                
                # 计算文件哈希
                file_hash = await self._calculate_file_hash(str(file_path))
                
                # 提取元数据
                metadata = {}
                if rule.extract_metadata:
                    metadata = await MediaMetadataExtractor.extract_metadata_async(
                        str(file_path),
                        mode=rule.metadata_mode or 'lightweight',
                        timeout=rule.metadata_timeout or 10
                    )
                
                # 创建媒体文件记录
                sender_info = SenderFilter.get_sender_info(message)
                
                media_file = MediaFile(
                    monitor_rule_id=rule.id,
                    download_task_id=task.id,
                    message_id=message.id,
                    temp_path=str(file_path),
                    file_hash=file_hash,
                    file_name=task.file_name,
                    file_type=task.file_type,
                    file_size_mb=task.file_size_mb,
                    extension=Path(task.file_name).suffix,
                    original_name=task.file_name,
                    metadata=json.dumps(metadata) if metadata else None,
                    width=metadata.get('width'),
                    height=metadata.get('height'),
                    duration_seconds=metadata.get('duration_seconds'),
                    resolution=metadata.get('resolution'),
                    codec=metadata.get('codec'),
                    bitrate_kbps=metadata.get('bitrate_kbps'),
                    source_chat=str(message.chat_id) if hasattr(message, 'chat_id') else None,
                    sender_id=sender_info['id'],
                    sender_username=sender_info['username'],
                    is_organized=False,
                    is_uploaded_to_cloud=False
                )
                
                db.add(media_file)
                
                # 更新任务状态
                task.status = 'success'
                task.completed_at = datetime.now()
                task.progress_percent = 100
                
                # 更新规则统计
                rule.total_downloaded = (rule.total_downloaded or 0) + 1
                rule.total_size_mb = (rule.total_size_mb or 0) + task.file_size_mb
                rule.last_download_at = datetime.now()
                
                await db.commit()
                
                logger.info(f"🎉 下载任务完成: {task.file_name}")
                
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

