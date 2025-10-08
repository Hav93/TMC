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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from database import get_db
from models import MediaMonitorRule, DownloadTask, MediaFile
from utils.media_filters import MediaFilter, SenderFilter
from utils.media_metadata import MediaMetadataExtractor

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp 未安装，CloudDrive API 功能将不可用")


class CloudDriveClient:
    """CloudDrive Web API 客户端"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
    
    async def login(self) -> bool:
        """登录并获取 token"""
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp 未安装，无法使用 CloudDrive API")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                login_data = {
                    'username': self.username,
                    'password': self.password
                }
                
                async with session.post(
                    f"{self.base_url}/api/auth/login",
                    json=login_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        self.token = result.get('token') or result.get('access_token')
                        logger.info("✅ CloudDrive 登录成功")
                        return True
                    else:
                        logger.error(f"CloudDrive 登录失败: HTTP {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"CloudDrive 登录异常: {e}")
            return False
    
    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        on_progress=None
    ) -> Dict[str, Any]:
        """
        上传文件到 CloudDrive
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
            on_progress: 进度回调函数 callback(uploaded_bytes, total_bytes, progress_percent)
            
        Returns:
            {'success': bool, 'message': str, ...}
        """
        if not AIOHTTP_AVAILABLE:
            return {'success': False, 'message': 'aiohttp 未安装'}
        
        if not self.token:
            if not await self.login():
                return {'success': False, 'message': '登录失败'}
        
        try:
            file_size = os.path.getsize(local_path)
            filename = Path(local_path).name
            
            logger.info(f"☁️ 开始上传到 CloudDrive: {filename} ({file_size / 1024 / 1024:.2f} MB)")
            
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.token}'}
                
                # 方式1：尝试分块上传（如果 CloudDrive 支持）
                # 方式2：直接上传整个文件
                
                with open(local_path, 'rb') as f:
                    # 使用 multipart/form-data 上传
                    form = aiohttp.FormData()
                    form.add_field('file', f, filename=filename)
                    form.add_field('path', remote_path)
                    
                    async with session.post(
                        f"{self.base_url}/api/upload",
                        headers=headers,
                        data=form,
                        timeout=aiohttp.ClientTimeout(total=3600)  # 1小时超时
                    ) as resp:
                        if resp.status in [200, 201]:
                            logger.info(f"✅ CloudDrive 上传成功: {filename}")
                            return {
                                'success': True,
                                'message': '上传成功',
                                'remote_path': remote_path,
                                'size': file_size
                            }
                        else:
                            error_text = await resp.text()
                            logger.error(f"CloudDrive 上传失败: HTTP {resp.status}, {error_text}")
                            return {
                                'success': False,
                                'message': f'上传失败: HTTP {resp.status}'
                            }
                
        except Exception as e:
            logger.error(f"CloudDrive 上传异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'上传异常: {str(e)}'}


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
            sender = metadata.get('sender_username') or metadata.get('sender_id', 'unknown')
            return FileOrganizer._sanitize_path(sender)
        
        elif rule.folder_structure == 'custom':
            template = rule.custom_folder_template or '{year}/{month}/{type}'
            now = datetime.now()
            
            replacements = {
                '{year}': str(now.year),
                '{month}': f"{now.month:02d}",
                '{day}': f"{now.day:02d}",
                '{type}': metadata.get('type', 'other'),
                '{source}': FileOrganizer._sanitize_path(metadata.get('source_chat', 'unknown')),
                '{sender}': FileOrganizer._sanitize_path(
                    metadata.get('sender_username') or metadata.get('sender_id', 'unknown')
                ),
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
                metadata.get('sender_username') or metadata.get('sender_id', 'unknown')
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
            if rule.organize_target_type == 'local':
                base_path = Path(rule.organize_local_path or '/app/media/organized')
            elif rule.organize_target_type == 'clouddrive_mount':
                base_path = Path(rule.organize_clouddrive_mount or '/mnt/clouddrive')
            else:
                # clouddrive_api 模式先归档到本地
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
                
                # 实际下载文件
                client = task_data.get('client')
                message = task_data.get('message')
                
                if not client or not message:
                    raise Exception("缺少客户端或消息对象")
                
                # 使用 Telethon 下载媒体
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
                
                # 提取元数据
                metadata_dict = {}
                if rule.extract_metadata and rule.metadata_mode != 'disabled':
                    try:
                        if rule.async_metadata_extraction:
                            # 异步提取，不阻塞
                            metadata_dict = await MediaMetadataExtractor.extract_metadata_async(
                                str(file_path),
                                mode=rule.metadata_mode or 'lightweight',
                                timeout=rule.metadata_timeout or 10
                            )
                        else:
                            # 同步提取
                            metadata_dict = await MediaMetadataExtractor.extract_metadata_async(
                                str(file_path),
                                mode=rule.metadata_mode or 'lightweight',
                                timeout=rule.metadata_timeout or 10
                            )
                        
                        logger.info(f"📊 元数据提取完成: {metadata_dict.get('type', 'unknown')}")
                    except Exception as meta_error:
                        logger.warning(f"元数据提取失败: {meta_error}")
                        metadata_dict = {'error': str(meta_error)}
                
                # 获取发送者和来源信息
                sender_info = SenderFilter.get_sender_info(message)
                
                # 准备归档元数据
                organize_metadata = {
                    'type': task.file_type,
                    'sender_id': sender_info['id'],
                    'sender_username': sender_info['username'],
                    'source_chat': str(task.chat_id) if task.chat_id else 'unknown'
                }
                
                # 归档文件（如果启用）
                final_path = None
                if rule.organize_enabled:
                    final_path = await FileOrganizer.organize_file(
                        rule,
                        str(file_path),
                        organize_metadata
                    )
                    
                    if final_path:
                        logger.info(f"📦 文件已归档: {final_path}")
                
                # 上传到 CloudDrive（如果启用）
                clouddrive_path = None
                is_uploaded = False
                
                if rule.clouddrive_enabled and rule.organize_target_type == 'clouddrive_api':
                    try:
                        # 创建 CloudDrive 客户端
                        cloud_client = CloudDriveClient(
                            rule.clouddrive_url,
                            rule.clouddrive_username,
                            rule.clouddrive_password
                        )
                        
                        # 生成远程路径
                        remote_dir = FileOrganizer.generate_target_directory(rule, organize_metadata)
                        remote_filename = FileOrganizer.generate_filename(rule, task.file_name, organize_metadata)
                        clouddrive_path = os.path.join(
                            rule.clouddrive_remote_path or '/Media',
                            remote_dir,
                            remote_filename
                        )
                        
                        # 上传文件（使用归档后的文件或临时文件）
                        upload_file = final_path if final_path else str(file_path)
                        upload_result = await cloud_client.upload_file(
                            upload_file,
                            clouddrive_path
                        )
                        
                        if upload_result['success']:
                            is_uploaded = True
                            logger.info(f"☁️ 文件已上传到 CloudDrive: {clouddrive_path}")
                        else:
                            logger.warning(f"CloudDrive 上传失败: {upload_result['message']}")
                    
                    except Exception as cloud_error:
                        logger.error(f"CloudDrive 上传异常: {cloud_error}")
                
                # 创建媒体文件记录
                media_file = MediaFile(
                    monitor_rule_id=rule.id,
                    download_task_id=task.id,
                    message_id=message.id,
                    temp_path=str(file_path) if not final_path else None,
                    final_path=final_path,
                    clouddrive_path=clouddrive_path,
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
                    source_chat=str(task.chat_id) if task.chat_id else None,
                    sender_id=sender_info['id'],
                    sender_username=sender_info['username'],
                    is_organized=bool(final_path),
                    is_uploaded_to_cloud=is_uploaded,
                    organized_at=datetime.now() if final_path else None,
                    uploaded_at=datetime.now() if is_uploaded else None
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

