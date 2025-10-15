"""
115离线任务监控服务

功能：
1. 监控115离线下载任务
2. 任务状态轮询
3. 完成后自动处理
4. 失败任务重试
"""
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from log_manager import get_logger

logger = get_logger("offline_monitor", "enhanced_bot.log")


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"        # 等待中
    DOWNLOADING = "downloading"  # 下载中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
    PAUSED = "paused"          # 暂停


@dataclass
class OfflineTask:
    """离线任务"""
    task_id: str                    # 任务ID
    task_url: str                   # 下载URL
    task_name: str                  # 任务名称
    file_size: int                  # 文件大小
    status: TaskStatus              # 状态
    progress: float = 0.0           # 进度（0-100）
    download_speed: int = 0         # 下载速度（字节/秒）
    error_message: Optional[str] = None  # 错误信息
    created_at: Optional[datetime] = None  # 创建时间
    completed_at: Optional[datetime] = None  # 完成时间


class OfflineTaskMonitor:
    """
    115离线任务监控服务
    
    功能：
    1. 监控离线任务列表
    2. 定时轮询任务状态
    3. 完成后触发回调
    4. 失败任务重试
    """
    
    def __init__(self, check_interval: int = 60):
        """
        初始化监控服务
        
        Args:
            check_interval: 检查间隔（秒）
        """
        self.check_interval = check_interval
        self.tasks: Dict[str, OfflineTask] = {}
        self.is_running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self.callbacks = {
            "on_completed": [],
            "on_failed": [],
            "on_progress": []
        }
        
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_tasks": 0
        }
    
    def register_callback(self, event: str, callback):
        """
        注册回调函数
        
        Args:
            event: 事件类型（on_completed/on_failed/on_progress）
            callback: 回调函数
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)
            logger.info(f"✅ 注册回调: {event}")
    
    async def start(self):
        """启动监控"""
        if self.is_running:
            logger.warning("⚠️ 监控已在运行")
            return
        
        self.is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"✅ 离线任务监控已启动（间隔：{self.check_interval}秒）")
    
    async def stop(self):
        """停止监控"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ 离线任务监控已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                await self._check_tasks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 监控循环错误: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    async def _check_tasks(self):
        """检查所有任务"""
        if not self.tasks:
            return
        
        logger.debug(f"🔍 检查 {len(self.tasks)} 个离线任务")
        
        for task_id, task in list(self.tasks.items()):
            try:
                # 跳过已完成或失败的任务
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    continue
                
                # 更新任务状态（这里需要调用115 API）
                updated_task = await self._fetch_task_status(task_id)
                
                if updated_task:
                    # 检查状态变化
                    old_status = task.status
                    new_status = updated_task.status
                    
                    # 更新任务
                    self.tasks[task_id] = updated_task
                    
                    # 触发回调
                    if old_status != new_status:
                        if new_status == TaskStatus.COMPLETED:
                            await self._on_task_completed(updated_task)
                        elif new_status == TaskStatus.FAILED:
                            await self._on_task_failed(updated_task)
                    
                    # 进度回调
                    if new_status == TaskStatus.DOWNLOADING:
                        await self._on_task_progress(updated_task)
                
            except Exception as e:
                logger.error(f"❌ 检查任务失败: {task_id}, 错误: {e}")
    
    async def _fetch_task_status(self, task_id: str) -> Optional[OfflineTask]:
        """
        获取任务状态（需要调用115 API）
        
        Args:
            task_id: 任务ID
        
        Returns:
            OfflineTask: 更新后的任务
        """
        # TODO: 调用115 API获取真实状态
        # 这里是模拟实现
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        # 模拟进度更新
        if task.status == TaskStatus.DOWNLOADING:
            task.progress = min(task.progress + 10, 100)
            if task.progress >= 100:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
        
        return task
    
    async def _on_task_completed(self, task: OfflineTask):
        """任务完成回调"""
        logger.info(f"✅ 离线任务完成: {task.task_name}")
        
        # 更新统计
        self.stats["completed_tasks"] += 1
        self.stats["active_tasks"] = len([t for t in self.tasks.values() 
                                          if t.status == TaskStatus.DOWNLOADING])
        
        # 触发回调
        for callback in self.callbacks["on_completed"]:
            try:
                await callback(task)
            except Exception as e:
                logger.error(f"❌ 完成回调失败: {e}")
    
    async def _on_task_failed(self, task: OfflineTask):
        """任务失败回调"""
        logger.error(f"❌ 离线任务失败: {task.task_name}, 错误: {task.error_message}")
        
        # 更新统计
        self.stats["failed_tasks"] += 1
        self.stats["active_tasks"] = len([t for t in self.tasks.values() 
                                          if t.status == TaskStatus.DOWNLOADING])
        
        # 触发回调
        for callback in self.callbacks["on_failed"]:
            try:
                await callback(task)
            except Exception as e:
                logger.error(f"❌ 失败回调失败: {e}")
    
    async def _on_task_progress(self, task: OfflineTask):
        """任务进度回调"""
        # 触发回调
        for callback in self.callbacks["on_progress"]:
            try:
                await callback(task)
            except Exception as e:
                logger.error(f"❌ 进度回调失败: {e}")
    
    async def add_task(self, task_url: str, task_name: str = "") -> str:
        """
        添加离线任务
        
        Args:
            task_url: 下载URL（磁力链接或HTTP链接）
            task_name: 任务名称
        
        Returns:
            str: 任务ID
        """
        # TODO: 调用115 API添加离线任务
        # 这里是模拟实现
        task_id = f"task_{len(self.tasks) + 1}"
        
        task = OfflineTask(
            task_id=task_id,
            task_url=task_url,
            task_name=task_name or f"Task {task_id}",
            file_size=0,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        self.stats["total_tasks"] += 1
        
        logger.info(f"✅ 添加离线任务: {task_name} ({task_id})")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[OfflineTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[OfflineTask]:
        """获取所有任务"""
        return list(self.tasks.values())
    
    def get_active_tasks(self) -> List[OfflineTask]:
        """获取活跃任务"""
        return [t for t in self.tasks.values() 
                if t.status in [TaskStatus.PENDING, TaskStatus.DOWNLOADING]]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "check_interval": self.check_interval,
            "is_running": self.is_running
        }


# 全局单例
_offline_monitor: Optional[OfflineTaskMonitor] = None


def get_offline_monitor(check_interval: int = 60) -> OfflineTaskMonitor:
    """获取离线任务监控单例"""
    global _offline_monitor
    if _offline_monitor is None:
        _offline_monitor = OfflineTaskMonitor(check_interval)
    return _offline_monitor


# 便捷函数
async def add_offline_task(task_url: str, task_name: str = "") -> str:
    """
    添加离线任务
    
    Args:
        task_url: 下载URL
        task_name: 任务名称
    
    Returns:
        str: 任务ID
    """
    monitor = get_offline_monitor()
    return await monitor.add_task(task_url, task_name)


def get_offline_task(task_id: str) -> Optional[OfflineTask]:
    """
    获取离线任务
    
    Args:
        task_id: 任务ID
    
    Returns:
        OfflineTask: 任务信息
    """
    monitor = get_offline_monitor()
    return monitor.get_task(task_id)

