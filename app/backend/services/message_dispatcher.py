"""
消息分发器

统一管理所有消息处理器，并发执行，收集处理结果
"""
from typing import List, Dict, Any
import asyncio
import time
from log_manager import get_logger

logger = get_logger("message_dispatcher", "enhanced_bot.log")


class MessageProcessor:
    """消息处理器基类"""
    
    async def should_process(self, context: 'MessageContext') -> bool:
        """判断是否应该处理这条消息"""
        raise NotImplementedError
    
    async def process(self, context: 'MessageContext') -> bool:
        """处理消息，返回是否成功"""
        raise NotImplementedError


class MessageDispatcher:
    """
    消息分发器
    
    作用：
    1. 统一管理所有处理器
    2. 并发执行处理器
    3. 收集处理结果
    4. 性能监控
    """
    
    def __init__(self):
        self.processors: List[MessageProcessor] = []
        self.stats = {
            'total_messages': 0,
            'total_processing_time': 0,
            'processor_stats': {}
        }
    
    def register(self, processor: MessageProcessor):
        """注册处理器"""
        self.processors.append(processor)
        processor_name = processor.__class__.__name__
        self.stats['processor_stats'][processor_name] = {
            'processed': 0,
            'success': 0,
            'failed': 0,
            'avg_time': 0
        }
        logger.info(f"✅ 注册处理器: {processor_name}")
    
    async def dispatch(self, context: 'MessageContext') -> Dict[str, bool]:
        """
        分发消息给所有处理器
        
        返回：{processor_name: success}
        """
        start_time = time.time()
        self.stats['total_messages'] += 1
        
        # 1. 筛选需要处理的处理器
        active_processors = []
        for processor in self.processors:
            try:
                if await processor.should_process(context):
                    active_processors.append(processor)
            except Exception as e:
                logger.error(f"处理器 {processor.__class__.__name__} 判断失败: {e}")
        
        if not active_processors:
            logger.debug(f"没有处理器需要处理此消息: chat_id={context.chat_id}")
            return {}
        
        logger.info(f"📨 分发消息: chat_id={context.chat_id}, 激活处理器={len(active_processors)}")
        
        # 2. 并发执行所有处理器
        tasks = []
        for processor in active_processors:
            task = asyncio.create_task(
                self._process_with_stats(processor, context)
            )
            tasks.append((processor.__class__.__name__, task))
        
        # 3. 等待所有处理器完成
        results = {}
        for processor_name, task in tasks:
            try:
                success = await task
                results[processor_name] = success
            except Exception as e:
                logger.error(f"处理器 {processor_name} 执行失败: {e}")
                results[processor_name] = False
        
        # 4. 更新统计
        processing_time = (time.time() - start_time) * 1000
        self.stats['total_processing_time'] += processing_time
        
        if processing_time > 500:  # 超过500ms记录警告
            logger.warning(f"消息处理耗时过长: {processing_time:.2f}ms")
        
        return results
    
    async def _process_with_stats(self, processor: MessageProcessor, context: 'MessageContext') -> bool:
        """执行处理器并记录统计"""
        processor_name = processor.__class__.__name__
        stats = self.stats['processor_stats'][processor_name]
        
        start_time = time.time()
        stats['processed'] += 1
        
        try:
            success = await processor.process(context)
            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
            
            # 更新平均处理时间
            processing_time = (time.time() - start_time) * 1000
            stats['avg_time'] = (
                (stats['avg_time'] * (stats['processed'] - 1) + processing_time) 
                / stats['processed']
            )
            
            logger.debug(f"处理器 {processor_name} 完成: success={success}, 耗时={processing_time:.2f}ms")
            return success
            
        except Exception as e:
            stats['failed'] += 1
            logger.error(f"处理器 {processor_name} 执行异常: {e}", exc_info=True)
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        return {
            'total_messages': self.stats['total_messages'],
            'avg_processing_time': (
                self.stats['total_processing_time'] / self.stats['total_messages']
                if self.stats['total_messages'] > 0 else 0
            ),
            'processors': self.stats['processor_stats']
        }


# 全局消息分发器实例
_dispatcher = None

def get_message_dispatcher() -> MessageDispatcher:
    """获取全局消息分发器实例"""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = MessageDispatcher()
        logger.info("✅ 创建全局消息分发器")
    return _dispatcher

