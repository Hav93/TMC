"""
批量数据库写入器

功能：
1. 批量写入数据库，减少IO次数
2. 自动刷新机制（时间/数量触发）
3. 支持多种数据模型
4. 错误处理和重试
"""
from typing import Dict, List, Any, Type, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, update
from log_manager import get_logger
from database import get_db

logger = get_logger("batch_writer", "enhanced_bot.log")


@dataclass
class BatchOperation:
    """批量操作"""
    operation_type: str  # 'insert' or 'update'
    model: Type
    data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)


class BatchDatabaseWriter:
    """
    批量数据库写入器
    
    特性：
    1. 批量插入/更新
    2. 自动刷新（时间/数量触发）
    3. 按模型分组
    4. 性能统计
    """
    
    def __init__(
        self,
        batch_size: int = 50,
        flush_interval: int = 10,  # 秒
        max_queue_size: int = 1000
    ):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_queue_size = max_queue_size
        
        # 操作队列（按模型分组）
        self._queues: Dict[str, List[BatchOperation]] = {}
        self._lock = asyncio.Lock()
        
        # 运行状态
        self._is_running = False
        self._flush_task: Optional[asyncio.Task] = None
        
        # 统计信息
        self.stats = {
            'total_operations': 0,
            'total_inserts': 0,
            'total_updates': 0,
            'total_flushes': 0,
            'total_errors': 0,
            'current_queue_size': 0
        }
    
    async def start(self):
        """启动批量写入器"""
        if self._is_running:
            return
        
        self._is_running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info(f"✅ 批量数据库写入器已启动 (batch_size={self.batch_size}, flush_interval={self.flush_interval}s)")
    
    async def stop(self):
        """停止批量写入器"""
        self._is_running = False
        
        # 刷新所有待处理的数据
        await self.flush_all()
        
        # 停止刷新任务
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ 批量数据库写入器已停止")
    
    async def add_insert(self, model: Type, data: Dict[str, Any]):
        """添加插入操作"""
        await self._add_operation('insert', model, data)
    
    async def add_update(self, model: Type, data: Dict[str, Any]):
        """添加更新操作"""
        await self._add_operation('update', model, data)
    
    async def _add_operation(self, operation_type: str, model: Type, data: Dict[str, Any]):
        """添加操作到队列"""
        async with self._lock:
            model_name = model.__tablename__
            
            # 初始化队列
            if model_name not in self._queues:
                self._queues[model_name] = []
            
            # 检查队列大小
            if len(self._queues[model_name]) >= self.max_queue_size:
                logger.warning(f"队列已满，立即刷新: {model_name}")
                await self._flush_model(model_name)
            
            # 添加操作
            operation = BatchOperation(
                operation_type=operation_type,
                model=model,
                data=data
            )
            self._queues[model_name].append(operation)
            
            self.stats['total_operations'] += 1
            self.stats['current_queue_size'] = sum(len(q) for q in self._queues.values())
            
            # 检查是否需要刷新
            if len(self._queues[model_name]) >= self.batch_size:
                logger.debug(f"达到批量大小，刷新队列: {model_name}")
                await self._flush_model(model_name)
    
    async def _flush_loop(self):
        """定期刷新循环"""
        while self._is_running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"刷新循环错误: {e}", exc_info=True)
    
    async def flush_all(self):
        """刷新所有队列"""
        async with self._lock:
            model_names = list(self._queues.keys())
        
        for model_name in model_names:
            try:
                await self._flush_model(model_name)
            except Exception as e:
                logger.error(f"刷新模型 {model_name} 失败: {e}", exc_info=True)
    
    async def _flush_model(self, model_name: str):
        """刷新指定模型的队列"""
        async with self._lock:
            if model_name not in self._queues or not self._queues[model_name]:
                return
            
            operations = self._queues[model_name]
            self._queues[model_name] = []
            self.stats['current_queue_size'] = sum(len(q) for q in self._queues.values())
        
        if not operations:
            return
        
        logger.info(f"刷新队列: {model_name}, 操作数: {len(operations)}")
        
        # 按操作类型分组
        inserts = [op for op in operations if op.operation_type == 'insert']
        updates = [op for op in operations if op.operation_type == 'update']
        
        # 执行批量操作
        try:
            async for db in get_db():
                # 批量插入
                if inserts:
                    await self._batch_insert(db, inserts)
                
                # 批量更新
                if updates:
                    await self._batch_update(db, updates)
                
                # 提交
                await db.commit()
                
                self.stats['total_flushes'] += 1
                self.stats['total_inserts'] += len(inserts)
                self.stats['total_updates'] += len(updates)
                
                logger.info(
                    f"✅ 批量写入完成: {model_name}, "
                    f"插入={len(inserts)}, 更新={len(updates)}"
                )
                break
        
        except Exception as e:
            logger.error(f"批量写入失败: {model_name}, 错误: {e}", exc_info=True)
            self.stats['total_errors'] += 1
            
            # 失败时，尝试逐条写入
            await self._fallback_write(operations)
    
    async def _batch_insert(self, db: AsyncSession, operations: List[BatchOperation]):
        """批量插入"""
        if not operations:
            return
        
        model = operations[0].model
        data_list = [op.data for op in operations]
        
        try:
            stmt = insert(model).values(data_list)
            await db.execute(stmt)
        except Exception as e:
            logger.error(f"批量插入失败: {model.__tablename__}, 错误: {e}")
            raise
    
    async def _batch_update(self, db: AsyncSession, operations: List[BatchOperation]):
        """
        批量更新（优化版）
        
        策略：
        1. 按更新字段分组
        2. 使用bulk_update_mappings进行真正的批量更新
        3. 回退到逐条更新（如果批量失败）
        """
        if not operations:
            return
        
        model = operations[0].model
        
        # 准备批量更新数据
        update_mappings = []
        for operation in operations:
            data = operation.data.copy()
            
            # 检查是否有id字段
            if 'id' not in data:
                logger.warning(f"更新操作缺少id字段: {model.__tablename__}")
                continue
            
            update_mappings.append(data)
        
        if not update_mappings:
            return
        
        try:
            # 使用bulk_update_mappings进行批量更新
            await db.run_sync(
                lambda session: session.bulk_update_mappings(model, update_mappings)
            )
            logger.debug(f"批量更新成功: {model.__tablename__}, 数量={len(update_mappings)}")
            
        except Exception as e:
            logger.warning(f"批量更新失败，回退到逐条更新: {e}")
            
            # 回退到逐条更新
            for operation in operations:
                try:
                    data = operation.data.copy()
                    
                    if 'id' not in data:
                        continue
                    
                    record_id = data.pop('id')
                    stmt = update(model).where(model.id == record_id).values(**data)
                    await db.execute(stmt)
                
                except Exception as update_error:
                    logger.error(f"逐条更新失败: {update_error}")
                    continue
    
    async def _fallback_write(self, operations: List[BatchOperation]):
        """回退：逐条写入"""
        logger.info(f"使用回退模式，逐条写入 {len(operations)} 条记录")
        
        success_count = 0
        fail_count = 0
        
        for operation in operations:
            try:
                async for db in get_db():
                    if operation.operation_type == 'insert':
                        record = operation.model(**operation.data)
                        db.add(record)
                    elif operation.operation_type == 'update':
                        data = operation.data.copy()
                        if 'id' in data:
                            record_id = data.pop('id')
                            stmt = update(operation.model).where(
                                operation.model.id == record_id
                            ).values(**data)
                            await db.execute(stmt)
                    
                    await db.commit()
                    success_count += 1
                    break
            
            except Exception as e:
                logger.error(f"逐条写入失败: {e}")
                fail_count += 1
        
        logger.info(f"回退写入完成: 成功={success_count}, 失败={fail_count}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'current_queue_size': self.stats['current_queue_size'],
            'total_operations': self.stats['total_operations'],
            'total_inserts': self.stats['total_inserts'],
            'total_updates': self.stats['total_updates'],
            'total_flushes': self.stats['total_flushes'],
            'total_errors': self.stats['total_errors'],
            'batch_size': self.batch_size,
            'flush_interval': self.flush_interval
        }
    
    async def get_queue_status(self) -> Dict[str, int]:
        """获取各模型队列状态"""
        async with self._lock:
            return {
                model_name: len(queue)
                for model_name, queue in self._queues.items()
            }


# 全局批量写入器实例
_batch_writer: Optional[BatchDatabaseWriter] = None


def get_batch_writer() -> BatchDatabaseWriter:
    """获取全局批量写入器实例"""
    global _batch_writer
    if _batch_writer is None:
        _batch_writer = BatchDatabaseWriter()
        logger.info("✅ 创建全局批量数据库写入器")
    return _batch_writer


async def init_batch_writer():
    """初始化批量写入器"""
    writer = get_batch_writer()
    await writer.start()
    return writer

