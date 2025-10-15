"""
性能监控API

提供缓存、重试队列、批量写入器的统计信息
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from api.dependencies import get_current_user
from log_manager import get_logger

logger = get_logger('performance_api')

router = APIRouter(tags=["性能监控"])


@router.get("/stats")
async def get_performance_stats(
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取性能统计信息
    
    返回：
    - 消息缓存统计
    - 过滤引擎统计
    - 重试队列统计
    - 批量写入器统计
    - 消息分发器统计
    """
    try:
        from services.common.message_cache import get_message_cache
        from services.common.filter_engine import get_filter_engine
        from services.common.retry_queue import get_retry_queue
        from services.common.batch_writer import get_batch_writer
        from services.message_dispatcher import get_message_dispatcher
        
        # 获取各组件统计
        cache_stats = get_message_cache().get_stats()
        filter_stats = get_filter_engine().get_stats()
        retry_stats = get_retry_queue().get_stats()
        batch_stats = get_batch_writer().get_stats()
        dispatcher_stats = get_message_dispatcher().get_stats()
        
        return {
            "success": True,
            "data": {
                "message_cache": cache_stats,
                "filter_engine": filter_stats,
                "retry_queue": retry_stats,
                "batch_writer": batch_stats,
                "message_dispatcher": dispatcher_stats
            }
        }
    
    except Exception as e:
        logger.error(f"获取性能统计失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取缓存统计信息"""
    try:
        from services.common.message_cache import get_message_cache
        cache = get_message_cache()
        
        return {
            "success": True,
            "data": cache.get_stats()
        }
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        return {"success": False, "error": str(e)}


@router.post("/cache/clear")
async def clear_cache(
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """清空缓存"""
    try:
        from services.common.message_cache import get_message_cache
        cache = get_message_cache()
        await cache.clear()
        
        return {
            "success": True,
            "message": "缓存已清空"
        }
    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        return {"success": False, "error": str(e)}


@router.get("/retry-queue/stats")
async def get_retry_queue_stats(
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取重试队列统计信息"""
    try:
        from services.common.retry_queue import get_retry_queue
        queue = get_retry_queue()
        
        stats = queue.get_stats()
        queue_status = await queue.get_queue_status()
        
        return {
            "success": True,
            "data": {
                **stats,
                "queue_by_type": queue_status
            }
        }
    except Exception as e:
        logger.error(f"获取重试队列统计失败: {e}")
        return {"success": False, "error": str(e)}


@router.get("/batch-writer/stats")
async def get_batch_writer_stats(
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取批量写入器统计信息"""
    try:
        from services.common.batch_writer import get_batch_writer
        writer = get_batch_writer()
        
        stats = writer.get_stats()
        queue_status = await writer.get_queue_status()
        
        return {
            "success": True,
            "data": {
                **stats,
                "queue_by_model": queue_status
            }
        }
    except Exception as e:
        logger.error(f"获取批量写入器统计失败: {e}")
        return {"success": False, "error": str(e)}


@router.post("/batch-writer/flush")
async def flush_batch_writer(
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """手动刷新批量写入器"""
    try:
        from services.common.batch_writer import get_batch_writer
        writer = get_batch_writer()
        await writer.flush_all()
        
        return {
            "success": True,
            "message": "批量写入器已刷新"
        }
    except Exception as e:
        logger.error(f"刷新批量写入器失败: {e}")
        return {"success": False, "error": str(e)}


@router.get("/filter-engine/stats")
async def get_filter_engine_stats(
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取过滤引擎统计信息"""
    try:
        from services.common.filter_engine import get_filter_engine
        engine = get_filter_engine()
        
        return {
            "success": True,
            "data": engine.get_stats()
        }
    except Exception as e:
        logger.error(f"获取过滤引擎统计失败: {e}")
        return {"success": False, "error": str(e)}


@router.post("/filter-engine/clear-cache")
async def clear_filter_cache(
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """清空过滤引擎缓存"""
    try:
        from services.common.filter_engine import get_filter_engine
        engine = get_filter_engine()
        engine.clear_cache()
        
        return {
            "success": True,
            "message": "过滤引擎缓存已清空"
        }
    except Exception as e:
        logger.error(f"清空过滤引擎缓存失败: {e}")
        return {"success": False, "error": str(e)}

