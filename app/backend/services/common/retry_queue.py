"""
智能重试队列

功能：
1. 失败任务自动重试
2. 指数退避策略
3. 最大重试次数限制
4. 优先级支持
5. 磁盘持久化（防止数据丢失）
"""
from typing import Dict, Any, Optional, Callable, Awaitable, List
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import heapq
import json
import os
from pathlib import Path
from log_manager import get_logger

logger = get_logger("retry_queue", "enhanced_bot.log")


class RetryStrategy(str, Enum):
    """重试策略"""
    IMMEDIATE = "immediate"  # 立即重试
    LINEAR = "linear"  # 线性退避（固定延迟）
    EXPONENTIAL = "exponential"  # 指数退避
    FIBONACCI = "fibonacci"  # 斐波那契退避


@dataclass(order=True)
class RetryTask:
    """重试任务"""
    # 任务数据（必须的字段）
    task_id: str = field(compare=False)
    task_type: str = field(compare=False)
    
    # 用于优先级队列排序的字段
    next_retry_time: datetime = field(compare=True)
    priority: int = field(compare=True, default=5)
    
    # 任务数据（可选）
    task_data: Dict[str, Any] = field(compare=False, default_factory=dict)
    
    # 重试信息
    retry_count: int = field(compare=False, default=0)
    max_retries: int = field(compare=False, default=3)
    strategy: RetryStrategy = field(compare=False, default=RetryStrategy.EXPONENTIAL)
    base_delay: int = field(compare=False, default=60)  # 基础延迟（秒）
    
    # 错误信息
    last_error: Optional[str] = field(compare=False, default=None)
    error_history: list = field(compare=False, default_factory=list)
    
    # 时间戳
    created_at: datetime = field(compare=False, default_factory=datetime.now)
    last_retry_at: Optional[datetime] = field(compare=False, default=None)
    
    def calculate_next_delay(self) -> int:
        """计算下次重试延迟（秒）"""
        if self.strategy == RetryStrategy.IMMEDIATE:
            return 0
        
        elif self.strategy == RetryStrategy.LINEAR:
            return self.base_delay
        
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            # 指数退避: base_delay * 2^retry_count
            return self.base_delay * (2 ** self.retry_count)
        
        elif self.strategy == RetryStrategy.FIBONACCI:
            # 斐波那契退避
            fib_sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
            index = min(self.retry_count, len(fib_sequence) - 1)
            return self.base_delay * fib_sequence[index]
        
        return self.base_delay
    
    def should_retry(self) -> bool:
        """判断是否应该重试"""
        return self.retry_count < self.max_retries
    
    def record_error(self, error: str):
        """记录错误"""
        self.last_error = error
        self.error_history.append({
            'error': error,
            'time': datetime.now().isoformat(),
            'retry_count': self.retry_count
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'task_data': self.task_data,
            'priority': self.priority,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'strategy': self.strategy.value,
            'base_delay': self.base_delay,
            'next_retry_time': self.next_retry_time.isoformat(),
            'last_error': self.last_error,
            'error_history': self.error_history,
            'created_at': self.created_at.isoformat(),
            'last_retry_at': self.last_retry_at.isoformat() if self.last_retry_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RetryTask':
        """从字典反序列化"""
        return cls(
            task_id=data['task_id'],
            task_type=data['task_type'],
            task_data=data['task_data'],
            priority=data['priority'],
            retry_count=data['retry_count'],
            max_retries=data['max_retries'],
            strategy=RetryStrategy(data['strategy']),
            base_delay=data['base_delay'],
            next_retry_time=datetime.fromisoformat(data['next_retry_time']),
            last_error=data.get('last_error'),
            error_history=data.get('error_history', []),
            created_at=datetime.fromisoformat(data['created_at']),
            last_retry_at=datetime.fromisoformat(data['last_retry_at']) if data.get('last_retry_at') else None
        )


class SmartRetryQueue:
    """
    智能重试队列
    
    特性：
    1. 优先级队列
    2. 多种重试策略
    3. 自动调度
    4. 统计监控
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        check_interval: int = 10,  # 检查间隔（秒）
        persistence_enabled: bool = True,
        persistence_path: str = "data/retry_queue.json",
        persistence_interval: int = 60  # 持久化间隔（秒）
    ):
        self.max_concurrent = max_concurrent
        self.check_interval = check_interval
        self.persistence_enabled = persistence_enabled
        self.persistence_path = persistence_path
        self.persistence_interval = persistence_interval
        
        # 优先级队列（最小堆）
        self._queue: List[RetryTask] = []
        self._lock = asyncio.Lock()
        
        # 任务处理器注册表
        self._handlers: Dict[str, Callable[[RetryTask], Awaitable[bool]]] = {}
        
        # 运行状态
        self._is_running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._scheduler_task: Optional[asyncio.Task] = None
        self._persistence_task: Optional[asyncio.Task] = None
        
        # 统计信息
        self.stats = {
            'total_added': 0,
            'total_retried': 0,
            'total_success': 0,
            'total_failed': 0,
            'total_abandoned': 0,
            'current_queue_size': 0,
            'last_persistence': None,
            'persistence_errors': 0
        }
    
    def register_handler(
        self,
        task_type: str,
        handler: Callable[[RetryTask], Awaitable[bool]]
    ):
        """
        注册任务处理器
        
        handler 应该返回 True（成功）或 False（失败）
        """
        self._handlers[task_type] = handler
        logger.info(f"✅ 注册重试处理器: {task_type}")
    
    async def start(self):
        """启动重试队列"""
        if self._is_running:
            return
        
        self._is_running = True
        
        # 从磁盘加载队列
        if self.persistence_enabled:
            await self._load_from_disk()
        
        # 启动调度器
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        # 启动工作线程
        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._worker_loop(i))
            self._worker_tasks.append(task)
        
        # 启动持久化任务
        if self.persistence_enabled:
            self._persistence_task = asyncio.create_task(self._persistence_loop())
        
        logger.info(
            f"✅ 智能重试队列已启动 (workers={self.max_concurrent}, "
            f"persistence={'enabled' if self.persistence_enabled else 'disabled'})"
        )
    
    async def stop(self):
        """停止重试队列"""
        self._is_running = False
        
        # 保存队列到磁盘
        if self.persistence_enabled:
            await self._save_to_disk()
        
        # 停止持久化任务
        if self._persistence_task:
            self._persistence_task.cancel()
            try:
                await self._persistence_task
            except asyncio.CancelledError:
                pass
        
        # 停止调度器
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # 停止工作线程
        for task in self._worker_tasks:
            task.cancel()
        
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()
        
        logger.info("✅ 智能重试队列已停止")
    
    async def add_task(
        self,
        task_id: str,
        task_type: str,
        task_data: Dict[str, Any],
        priority: int = 5,
        max_retries: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        base_delay: int = 60
    ):
        """添加重试任务"""
        async with self._lock:
            task = RetryTask(
                task_id=task_id,
                task_type=task_type,
                task_data=task_data,
                priority=priority,
                max_retries=max_retries,
                strategy=strategy,
                base_delay=base_delay,
                next_retry_time=datetime.now()  # 立即可重试
            )
            
            heapq.heappush(self._queue, task)
            self.stats['total_added'] += 1
            self.stats['current_queue_size'] = len(self._queue)
            
            logger.info(f"添加重试任务: {task_id} (type={task_type}, priority={priority})")
    
    async def _scheduler_loop(self):
        """调度器循环"""
        while self._is_running:
            try:
                await asyncio.sleep(self.check_interval)
                await self._check_ready_tasks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"调度器错误: {e}", exc_info=True)
    
    async def _check_ready_tasks(self):
        """检查准备好的任务"""
        async with self._lock:
            now = datetime.now()
            ready_count = 0
            
            # 统计准备好的任务数量
            for task in self._queue:
                if task.next_retry_time <= now:
                    ready_count += 1
            
            if ready_count > 0:
                logger.debug(f"发现 {ready_count} 个准备好的重试任务")
    
    async def _worker_loop(self, worker_id: int):
        """工作线程循环"""
        logger.info(f"👷 重试工作线程 #{worker_id+1} 已启动")
        
        while self._is_running:
            try:
                # 获取下一个准备好的任务
                task = await self._get_next_ready_task()
                
                if task is None:
                    # 没有准备好的任务，等待
                    await asyncio.sleep(1)
                    continue
                
                # 处理任务
                await self._process_task(task, worker_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Worker #{worker_id+1}] 处理任务失败: {e}", exc_info=True)
    
    async def _get_next_ready_task(self) -> Optional[RetryTask]:
        """获取下一个准备好的任务"""
        async with self._lock:
            now = datetime.now()
            
            # 查找第一个准备好的任务
            if self._queue and self._queue[0].next_retry_time <= now:
                task = heapq.heappop(self._queue)
                self.stats['current_queue_size'] = len(self._queue)
                return task
            
            return None
    
    async def _process_task(self, task: RetryTask, worker_id: int):
        """处理任务"""
        logger.info(f"[Worker #{worker_id+1}] 重试任务: {task.task_id} (第 {task.retry_count + 1} 次)")
        
        # 获取处理器
        handler = self._handlers.get(task.task_type)
        if handler is None:
            logger.error(f"未找到任务类型 {task.task_type} 的处理器")
            self.stats['total_failed'] += 1
            return
        
        # 执行处理器
        try:
            success = await handler(task)
            
            if success:
                # 成功
                logger.info(f"[Worker #{worker_id+1}] 任务成功: {task.task_id}")
                self.stats['total_success'] += 1
                self.stats['total_retried'] += 1
            else:
                # 失败，重新加入队列
                await self._handle_task_failure(task, "处理器返回失败")
        
        except Exception as e:
            # 异常，重新加入队列
            error_msg = f"处理器异常: {str(e)}"
            logger.error(f"[Worker #{worker_id+1}] {error_msg}", exc_info=True)
            await self._handle_task_failure(task, error_msg)
    
    async def _handle_task_failure(self, task: RetryTask, error: str):
        """处理任务失败"""
        task.retry_count += 1
        task.last_retry_at = datetime.now()
        task.record_error(error)
        
        if task.should_retry():
            # 计算下次重试时间
            delay = task.calculate_next_delay()
            task.next_retry_time = datetime.now() + timedelta(seconds=delay)
            
            # 重新加入队列
            async with self._lock:
                heapq.heappush(self._queue, task)
                self.stats['current_queue_size'] = len(self._queue)
            
            logger.warning(
                f"任务失败，将在 {delay}秒 后重试: {task.task_id} "
                f"(重试次数: {task.retry_count}/{task.max_retries})"
            )
        else:
            # 放弃重试
            logger.error(
                f"任务已达最大重试次数，放弃: {task.task_id} "
                f"(重试次数: {task.retry_count}/{task.max_retries})"
            )
            self.stats['total_abandoned'] += 1
            self.stats['total_failed'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'current_queue_size': self.stats['current_queue_size'],
            'total_added': self.stats['total_added'],
            'total_retried': self.stats['total_retried'],
            'total_success': self.stats['total_success'],
            'total_failed': self.stats['total_failed'],
            'total_abandoned': self.stats['total_abandoned'],
            'success_rate': (
                f"{(self.stats['total_success'] / self.stats['total_retried'] * 100):.2f}%"
                if self.stats['total_retried'] > 0 else "0.00%"
            )
        }
    
    async def get_queue_status(self) -> Dict[str, int]:
        """获取队列中各任务类型的数量"""
        async with self._lock:
            task_types: Dict[str, int] = {}
            for task in self._queue:
                task_type = task.task_type
                task_types[task_type] = task_types.get(task_type, 0) + 1
            return task_types
    
    # ===== 持久化相关方法 =====
    
    async def _persistence_loop(self):
        """定期持久化循环"""
        while self._is_running:
            try:
                await asyncio.sleep(self.persistence_interval)
                await self._save_to_disk()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"持久化循环错误: {e}", exc_info=True)
                self.stats['persistence_errors'] += 1
    
    async def _save_to_disk(self):
        """保存队列到磁盘"""
        try:
            async with self._lock:
                # 序列化队列
                queue_data = {
                    'version': '1.0',
                    'saved_at': datetime.now().isoformat(),
                    'tasks': [task.to_dict() for task in self._queue],
                    'stats': self.stats.copy()
                }
            
            # 确保目录存在
            path = Path(self.persistence_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入临时文件
            temp_path = f"{self.persistence_path}.tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(queue_data, f, indent=2, ensure_ascii=False)
            
            # 原子性替换
            os.replace(temp_path, self.persistence_path)
            
            self.stats['last_persistence'] = datetime.now().isoformat()
            logger.debug(f"队列已保存到磁盘: {len(queue_data['tasks'])} 个任务")
        
        except Exception as e:
            logger.error(f"保存队列到磁盘失败: {e}", exc_info=True)
            self.stats['persistence_errors'] += 1
    
    async def _load_from_disk(self):
        """从磁盘加载队列"""
        try:
            path = Path(self.persistence_path)
            if not path.exists():
                logger.info("未找到持久化文件，从空队列开始")
                return
            
            # 读取文件
            with open(path, 'r', encoding='utf-8') as f:
                queue_data = json.load(f)
            
            # 验证版本
            version = queue_data.get('version', '1.0')
            if version != '1.0':
                logger.warning(f"持久化文件版本不匹配: {version}, 跳过加载")
                return
            
            # 恢复任务
            tasks = queue_data.get('tasks', [])
            loaded_count = 0
            
            async with self._lock:
                for task_data in tasks:
                    try:
                        task = RetryTask.from_dict(task_data)
                        heapq.heappush(self._queue, task)
                        loaded_count += 1
                    except Exception as e:
                        logger.error(f"恢复任务失败: {e}")
                        continue
                
                self.stats['current_queue_size'] = len(self._queue)
            
            logger.info(
                f"✅ 从磁盘加载队列: {loaded_count}/{len(tasks)} 个任务, "
                f"保存时间: {queue_data.get('saved_at', 'unknown')}"
            )
        
        except Exception as e:
            logger.error(f"从磁盘加载队列失败: {e}", exc_info=True)
            # 不抛出异常，允许从空队列开始


# 全局重试队列实例
_retry_queue: Optional[SmartRetryQueue] = None


def get_retry_queue() -> SmartRetryQueue:
    """获取全局重试队列实例"""
    global _retry_queue
    if _retry_queue is None:
        _retry_queue = SmartRetryQueue()
        logger.info("✅ 创建全局智能重试队列")
    return _retry_queue


async def init_retry_queue():
    """初始化智能重试队列"""
    queue = get_retry_queue()
    await queue.start()
    return queue

