"""
媒体文件和下载任务 API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import Optional, List
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

from database import get_db
from models import MediaFile, DownloadTask, MediaMonitorRule
from core.logger import logger
from services.storage_manager import get_storage_manager

router = APIRouter(tags=["media_files"])


# ==================== 下载任务 API ====================

@router.get("/tasks")
async def get_download_tasks(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取下载任务列表"""
    try:
        query = select(DownloadTask)
        
        # 状态过滤
        if status:
            query = query.where(DownloadTask.status == status)
        
        # 总数
        total_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(total_query)
        
        # 按优先级和创建时间排序
        query = query.order_by(desc(DownloadTask.priority), DownloadTask.created_at)
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return {
            "success": True,
            "tasks": [task_to_dict(task) for task in tasks],
            "total": total or 0,
            "page": page,
            "page_size": page_size
        }
        
    except Exception as e:
        logger.error(f"获取下载任务列表失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"获取列表失败: {str(e)}"}
        )


@router.get("/tasks/stats")
async def get_task_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取下载任务统计"""
    try:
        # 按状态统计
        pending_count = await db.scalar(
            select(func.count(DownloadTask.id)).where(DownloadTask.status == 'pending')
        ) or 0
        
        downloading_count = await db.scalar(
            select(func.count(DownloadTask.id)).where(DownloadTask.status == 'downloading')
        ) or 0
        
        success_count = await db.scalar(
            select(func.count(DownloadTask.id)).where(DownloadTask.status == 'success')
        ) or 0
        
        failed_count = await db.scalar(
            select(func.count(DownloadTask.id)).where(DownloadTask.status == 'failed')
        ) or 0
        
        paused_count = await db.scalar(
            select(func.count(DownloadTask.id)).where(DownloadTask.status == 'paused')
        ) or 0
        
        return {
            "success": True,
            "stats": {
                "pending_count": pending_count,
                "downloading_count": downloading_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "paused_count": paused_count,
                "total_count": pending_count + downloading_count + success_count + failed_count + paused_count
            }
        }
        
    except Exception as e:
        logger.error(f"获取任务统计失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"获取统计失败: {str(e)}"}
        )


@router.post("/tasks/{task_id}/retry")
async def retry_download_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """重试下载任务"""
    try:
        result = await db.execute(
            select(DownloadTask).where(DownloadTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "任务不存在"}
            )
        
        # 重置任务状态
        task.status = 'pending'
        task.retry_count = 0
        task.last_error = None
        task.progress_percent = 0
        task.downloaded_bytes = 0
        
        await db.commit()
        
        logger.info(f"重试下载任务: {task.file_name} (ID: {task_id})")
        
        return {
            "success": True,
            "message": "任务已加入队列"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"重试下载任务失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"重试失败: {str(e)}"}
        )


@router.post("/tasks/retry-failed")
async def retry_all_failed_tasks(
    db: AsyncSession = Depends(get_db)
):
    """批量重试所有失败任务"""
    try:
        result = await db.execute(
            select(DownloadTask).where(DownloadTask.status == 'failed')
        )
        failed_tasks = result.scalars().all()
        
        count = 0
        for task in failed_tasks:
            task.status = 'pending'
            task.retry_count = 0
            task.last_error = None
            task.progress_percent = 0
            task.downloaded_bytes = 0
            count += 1
        
        await db.commit()
        
        logger.info(f"批量重试失败任务: {count} 个")
        
        return {
            "success": True,
            "message": f"已重试 {count} 个失败任务"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"批量重试失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"批量重试失败: {str(e)}"}
        )


@router.delete("/tasks/{task_id}")
async def delete_download_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除下载任务"""
    try:
        result = await db.execute(
            select(DownloadTask).where(DownloadTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "任务不存在"}
            )
        
        await db.delete(task)
        await db.commit()
        
        logger.info(f"删除下载任务: {task.file_name} (ID: {task_id})")
        
        return {
            "success": True,
            "message": "删除成功"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"删除下载任务失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"删除失败: {str(e)}"}
        )


@router.post("/tasks/{task_id}/priority")
async def update_task_priority(
    task_id: int,
    priority: int = Query(..., ge=-10, le=10),
    db: AsyncSession = Depends(get_db)
):
    """更新任务优先级"""
    try:
        result = await db.execute(
            select(DownloadTask).where(DownloadTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "任务不存在"}
            )
        
        task.priority = priority
        await db.commit()
        
        return {
            "success": True,
            "message": "优先级已更新"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"更新任务优先级失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"更新失败: {str(e)}"}
        )


# ==================== 媒体文件 API ====================

@router.get("/files")
async def get_media_files(
    keyword: Optional[str] = None,
    file_type: Optional[str] = None,
    monitor_rule: Optional[str] = None,
    organized: Optional[str] = None,
    cloud_status: Optional[str] = None,
    starred: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取媒体文件列表"""
    try:
        query = select(MediaFile)
        
        # 关键词搜索
        if keyword:
            query = query.where(
                or_(
                    MediaFile.file_name.contains(keyword),
                    MediaFile.original_name.contains(keyword)
                )
            )
        
        # 文件类型过滤
        if file_type and file_type != 'all':
            query = query.where(MediaFile.file_type == file_type)
        
        # 归档状态过滤
        if organized == 'organized':
            query = query.where(MediaFile.is_organized == True)
        elif organized == 'pending':
            query = query.where(MediaFile.is_organized == False)
        
        # 云端状态过滤
        if cloud_status == 'uploaded':
            query = query.where(MediaFile.is_uploaded_to_cloud == True)
        elif cloud_status == 'local':
            query = query.where(MediaFile.is_uploaded_to_cloud == False)
        
        # 收藏过滤
        if starred:
            query = query.where(MediaFile.is_starred == True)
        
        # 日期范围过滤
        if start_date:
            query = query.where(MediaFile.downloaded_at >= start_date)
        if end_date:
            query = query.where(MediaFile.downloaded_at <= end_date)
        
        # 总数
        total_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(total_query)
        
        # 分页查询
        query = query.order_by(desc(MediaFile.downloaded_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        files = result.scalars().all()
        
        return {
            "success": True,
            "files": [file_to_dict(file) for file in files],
            "total": total or 0,
            "page": page,
            "page_size": page_size
        }
        
    except Exception as e:
        logger.error(f"获取媒体文件列表失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"获取列表失败: {str(e)}"}
        )


@router.get("/files/stats")
async def get_media_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取媒体文件统计"""
    try:
        # 总体统计
        total_count = await db.scalar(select(func.count(MediaFile.id))) or 0
        total_size = await db.scalar(select(func.sum(MediaFile.file_size_mb))) or 0
        
        # 按类型统计
        by_type = {}
        for file_type in ['image', 'video', 'audio', 'document']:
            count = await db.scalar(
                select(func.count(MediaFile.id)).where(MediaFile.file_type == file_type)
            ) or 0
            size = await db.scalar(
                select(func.sum(MediaFile.file_size_mb)).where(MediaFile.file_type == file_type)
            ) or 0
            
            by_type[file_type] = {
                'count': count,
                'size_gb': round(size / 1024, 2)
            }
        
        # 其他统计
        organized_count = await db.scalar(
            select(func.count(MediaFile.id)).where(MediaFile.is_organized == True)
        ) or 0
        
        cloud_count = await db.scalar(
            select(func.count(MediaFile.id)).where(MediaFile.is_uploaded_to_cloud == True)
        ) or 0
        
        starred_count = await db.scalar(
            select(func.count(MediaFile.id)).where(MediaFile.is_starred == True)
        ) or 0
        
        return {
            "success": True,
            "stats": {
                "total_count": total_count,
                "total_size_gb": round(total_size / 1024, 2),
                "by_type": by_type,
                "organized_count": organized_count,
                "cloud_count": cloud_count,
                "starred_count": starred_count
            }
        }
        
    except Exception as e:
        logger.error(f"获取媒体统计失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"获取统计失败: {str(e)}"}
        )


@router.get("/files/{file_id}")
async def get_media_file_detail(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取媒体文件详情"""
    try:
        result = await db.execute(
            select(MediaFile).where(MediaFile.id == file_id)
        )
        file = result.scalar_one_or_none()
        
        if not file:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "文件不存在"}
            )
        
        return {
            "success": True,
            "file": file_to_dict(file)
        }
        
    except Exception as e:
        logger.error(f"获取文件详情失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"获取详情失败: {str(e)}"}
        )


@router.get("/download/{file_id}")
async def download_media_file(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """下载媒体文件"""
    try:
        result = await db.execute(
            select(MediaFile).where(MediaFile.id == file_id)
        )
        file = result.scalar_one_or_none()
        
        if not file:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "文件不存在"}
            )
        
        # 优先返回归档文件，否则返回临时文件
        file_path = file.final_path if file.is_organized and file.final_path else file.temp_path
        
        if not file_path or not os.path.exists(file_path):
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "文件已被删除"}
            )
        
        return FileResponse(
            file_path,
            filename=file.file_name,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"下载失败: {str(e)}"}
        )


@router.post("/files/{file_id}/star")
async def toggle_star(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """收藏/取消收藏文件"""
    try:
        result = await db.execute(
            select(MediaFile).where(MediaFile.id == file_id)
        )
        file = result.scalar_one_or_none()
        
        if not file:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "文件不存在"}
            )
        
        file.is_starred = not file.is_starred
        await db.commit()
        
        return {
            "success": True,
            "is_starred": file.is_starred
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"收藏文件失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"操作失败: {str(e)}"}
        )


@router.delete("/files/{file_id}")
async def delete_media_file(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除文件"""
    try:
        result = await db.execute(
            select(MediaFile).where(MediaFile.id == file_id)
        )
        file = result.scalar_one_or_none()
        
        if not file:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "文件不存在"}
            )
        
        # 删除物理文件
        for path in [file.temp_path, file.final_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    logger.info(f"删除文件: {path}")
                except Exception as e:
                    logger.warning(f"删除物理文件失败: {e}")
        
        # 删除数据库记录
        await db.delete(file)
        await db.commit()
        
        logger.info(f"删除媒体文件: {file.file_name} (ID: {file_id})")
        
        return {
            "success": True,
            "message": "删除成功"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"删除文件失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"删除失败: {str(e)}"}
        )


# ==================== 辅助函数 ====================

def task_to_dict(task: DownloadTask) -> dict:
    """将下载任务对象转换为字典"""
    return {
        "id": task.id,
        "monitor_rule_id": task.monitor_rule_id,
        "message_id": task.message_id,
        "chat_id": task.chat_id,
        "file_name": task.file_name,
        "file_type": task.file_type,
        "file_size_mb": task.file_size_mb,
        "status": task.status,
        "priority": task.priority,
        "downloaded_bytes": task.downloaded_bytes,
        "total_bytes": task.total_bytes,
        "progress_percent": task.progress_percent,
        "download_speed_mbps": task.download_speed_mbps,
        "retry_count": task.retry_count,
        "max_retries": task.max_retries,
        "last_error": task.last_error,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "failed_at": task.failed_at.isoformat() if task.failed_at else None
    }


def file_to_dict(file: MediaFile) -> dict:
    """将媒体文件对象转换为字典"""
    return {
        "id": file.id,
        "monitor_rule_id": file.monitor_rule_id,
        "download_task_id": file.download_task_id,
        "message_id": file.message_id,
        "temp_path": file.temp_path,
        "final_path": file.final_path,
        "clouddrive_path": file.clouddrive_path,
        "file_hash": file.file_hash,
        "file_name": file.file_name,
        "file_type": file.file_type,
        "file_size_mb": file.file_size_mb,
        "extension": file.extension,
        "original_name": file.original_name,
        "metadata": json.loads(file.metadata) if file.metadata else {},
        "width": file.width,
        "height": file.height,
        "duration_seconds": file.duration_seconds,
        "resolution": file.resolution,
        "codec": file.codec,
        "bitrate_kbps": file.bitrate_kbps,
        "source_chat": file.source_chat,
        "sender_id": file.sender_id,
        "sender_username": file.sender_username,
        "is_organized": file.is_organized,
        "is_uploaded_to_cloud": file.is_uploaded_to_cloud,
        "is_starred": file.is_starred,
        "downloaded_at": file.downloaded_at.isoformat() if file.downloaded_at else None,
        "organized_at": file.organized_at.isoformat() if file.organized_at else None,
        "uploaded_at": file.uploaded_at.isoformat() if file.uploaded_at else None
    }


# ==================== 存储管理 API ====================

@router.get("/storage/usage")
async def get_storage_usage(
    rule_id: Optional[int] = None
):
    """获取存储使用情况"""
    try:
        storage_manager = get_storage_manager()
        usage = await storage_manager.get_storage_usage(rule_id)
        return usage
    except Exception as e:
        logger.error(f"获取存储使用情况失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"获取失败: {str(e)}"}
        )


@router.post("/storage/cleanup")
async def manual_cleanup(
    rule_id: int = Query(..., description="规则ID"),
    days: int = Query(7, ge=1, le=365, description="保留天数"),
    only_organized: bool = Query(True, description="是否只清理已归档文件"),
    delete_db_records: bool = Query(False, description="是否删除数据库记录")
):
    """手动清理存储空间"""
    try:
        storage_manager = get_storage_manager()
        result = await storage_manager.manual_cleanup(
            rule_id=rule_id,
            days=days,
            only_organized=only_organized,
            delete_db_records=delete_db_records
        )
        return result
    except Exception as e:
        logger.error(f"手动清理失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"清理失败: {str(e)}"}
        )


@router.post("/storage/check")
async def check_storage(
    rule_id: int = Query(..., description="规则ID")
):
    """检查存储空间并根据需要自动清理"""
    try:
        storage_manager = get_storage_manager()
        result = await storage_manager.check_and_cleanup_if_needed(rule_id)
        return result
    except Exception as e:
        logger.error(f"存储检查失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"检查失败: {str(e)}"}
        )

