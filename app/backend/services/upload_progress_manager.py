"""
115上传进度管理器

支持实时进度更新和WebSocket推送
"""
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum


class UploadStatus(str, Enum):
    """上传状态"""
    PENDING = "pending"          # 待上传
    HASHING = "hashing"          # 计算哈希
    CHECKING = "checking"        # 检查秒传
    QUICK_SUCCESS = "quick_success"  # 秒传成功
    UPLOADING = "uploading"      # 上传中
    SUCCESS = "success"          # 上传成功
    FAILED = "failed"            # 上传失败
    CANCELLED = "cancelled"      # 已取消


class UploadProgress:
    """上传进度"""
    
    def __init__(
        self,
        file_path: str,
        file_name: str,
        file_size: int,
        target_dir_id: str = "0"
    ):
        self.file_path = file_path
        self.file_name = file_name
        self.file_size = file_size
        self.target_dir_id = target_dir_id
        
        # 进度信息
        self.status = UploadStatus.PENDING
        self.uploaded_bytes = 0
        self.total_bytes = file_size
        self.percentage = 0.0
        
        # 分片信息
        self.total_parts = 0
        self.uploaded_parts = 0
        
        # 速度计算
        self.start_time: Optional[datetime] = None
        self.last_update_time: Optional[datetime] = None
        self.speed_bytes_per_sec = 0.0
        
        # 结果信息
        self.error_message: Optional[str] = None
        self.file_id: Optional[str] = None
        self.is_quick_upload = False
    
    def start(self):
        """开始上传"""
        self.start_time = datetime.now()
        self.last_update_time = datetime.now()
        self.status = UploadStatus.UPLOADING
    
    def update(self, uploaded_bytes: int):
        """更新进度"""
        now = datetime.now()
        
        # 更新字节数
        self.uploaded_bytes = min(uploaded_bytes, self.total_bytes)
        self.percentage = (self.uploaded_bytes / self.total_bytes * 100) if self.total_bytes > 0 else 0
        
        # 计算速度
        if self.last_update_time:
            time_diff = (now - self.last_update_time).total_seconds()
            if time_diff > 0:
                bytes_diff = uploaded_bytes - (self.uploaded_bytes if hasattr(self, '_last_bytes') else 0)
                self.speed_bytes_per_sec = bytes_diff / time_diff
        
        self._last_bytes = uploaded_bytes
        self.last_update_time = now
    
    def update_parts(self, uploaded_parts: int, total_parts: int):
        """更新分片进度"""
        self.uploaded_parts = uploaded_parts
        self.total_parts = total_parts
        if total_parts > 0:
            self.percentage = (uploaded_parts / total_parts * 100)
    
    def complete(self, file_id: Optional[str] = None, is_quick: bool = False):
        """完成上传"""
        self.status = UploadStatus.QUICK_SUCCESS if is_quick else UploadStatus.SUCCESS
        self.percentage = 100.0
        self.uploaded_bytes = self.total_bytes
        self.file_id = file_id
        self.is_quick_upload = is_quick
    
    def fail(self, error_message: str):
        """上传失败"""
        self.status = UploadStatus.FAILED
        self.error_message = error_message
    
    def cancel(self):
        """取消上传"""
        self.status = UploadStatus.CANCELLED
    
    def get_elapsed_time(self) -> float:
        """获取已用时间（秒）"""
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_eta(self) -> Optional[float]:
        """获取预计剩余时间（秒）"""
        if self.speed_bytes_per_sec <= 0:
            return None
        remaining_bytes = self.total_bytes - self.uploaded_bytes
        return remaining_bytes / self.speed_bytes_per_sec
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'file_name': self.file_name,
            'file_size': self.file_size,
            'status': self.status.value,
            'percentage': round(self.percentage, 2),
            'uploaded_bytes': self.uploaded_bytes,
            'total_bytes': self.total_bytes,
            'total_parts': self.total_parts,
            'uploaded_parts': self.uploaded_parts,
            'speed_mbps': round(self.speed_bytes_per_sec / 1024 / 1024, 2),
            'elapsed_seconds': round(self.get_elapsed_time(), 1),
            'eta_seconds': round(self.get_eta(), 1) if self.get_eta() else None,
            'error_message': self.error_message,
            'file_id': self.file_id,
            'is_quick_upload': self.is_quick_upload,
        }


class UploadProgressManager:
    """
    上传进度管理器
    
    功能：
    1. 跟踪多个文件的上传进度
    2. 实时更新进度信息
    3. 支持进度回调（WebSocket推送）
    """
    
    def __init__(self):
        self._progresses: Dict[str, UploadProgress] = {}
        self._callbacks: Dict[str, list] = {}  # file_path -> [callback]
        self._lock = asyncio.Lock()
    
    async def create_progress(
        self,
        file_path: str,
        file_name: str,
        file_size: int,
        target_dir_id: str = "0"
    ) -> UploadProgress:
        """创建新的进度跟踪"""
        async with self._lock:
            progress = UploadProgress(file_path, file_name, file_size, target_dir_id)
            self._progresses[file_path] = progress
            return progress
    
    async def get_progress(self, file_path: str) -> Optional[UploadProgress]:
        """获取进度"""
        async with self._lock:
            return self._progresses.get(file_path)
    
    async def update_progress(
        self,
        file_path: str,
        uploaded_bytes: int
    ):
        """更新进度"""
        progress = await self.get_progress(file_path)
        if progress:
            progress.update(uploaded_bytes)
            await self._trigger_callbacks(file_path, progress)
    
    async def update_status(
        self,
        file_path: str,
        status: UploadStatus,
        **kwargs
    ):
        """更新状态"""
        progress = await self.get_progress(file_path)
        if progress:
            progress.status = status
            
            # 更新额外信息
            if 'error_message' in kwargs:
                progress.error_message = kwargs['error_message']
            if 'file_id' in kwargs:
                progress.file_id = kwargs['file_id']
            if 'is_quick' in kwargs:
                progress.is_quick_upload = kwargs['is_quick']
            
            await self._trigger_callbacks(file_path, progress)
    
    async def remove_progress(self, file_path: str):
        """移除进度"""
        async with self._lock:
            self._progresses.pop(file_path, None)
            self._callbacks.pop(file_path, None)
    
    async def list_progresses(self) -> Dict[str, UploadProgress]:
        """列出所有进度"""
        async with self._lock:
            return dict(self._progresses)
    
    def register_callback(
        self,
        file_path: str,
        callback: Callable[[UploadProgress], None]
    ):
        """注册进度回调"""
        if file_path not in self._callbacks:
            self._callbacks[file_path] = []
        self._callbacks[file_path].append(callback)
    
    def unregister_callback(
        self,
        file_path: str,
        callback: Callable[[UploadProgress], None]
    ):
        """注销进度回调"""
        if file_path in self._callbacks:
            try:
                self._callbacks[file_path].remove(callback)
            except ValueError:
                pass
    
    async def _trigger_callbacks(self, file_path: str, progress: UploadProgress):
        """触发所有回调"""
        if file_path in self._callbacks:
            for callback in self._callbacks[file_path]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(progress)
                    else:
                        callback(progress)
                except Exception as e:
                    print(f"进度回调异常: {e}")


# 全局管理器实例
_progress_manager: Optional[UploadProgressManager] = None


def get_progress_manager() -> UploadProgressManager:
    """获取全局进度管理器"""
    global _progress_manager
    if _progress_manager is None:
        _progress_manager = UploadProgressManager()
    return _progress_manager

