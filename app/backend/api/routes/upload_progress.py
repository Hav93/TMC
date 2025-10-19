"""
上传进度API路由
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from services.upload_progress_manager import get_progress_manager
from services.upload_resume_manager import get_resume_manager

router = APIRouter(prefix="/upload", tags=["upload"])


@router.get("/progress")
async def get_all_progress() -> Dict[str, Any]:
    """
    获取所有上传任务的进度
    
    Returns:
        {
            "uploads": [
                {
                    "file_name": "video.mp4",
                    "file_size": 1024000,
                    "status": "uploading",
                    "percentage": 45.5,
                    "speed_mbps": 2.5,
                    "eta_seconds": 120,
                    ...
                }
            ]
        }
    """
    try:
        progress_mgr = get_progress_manager()
        progresses = await progress_mgr.list_progresses()
        
        return {
            "uploads": [
                progress.to_dict()
                for progress in progresses.values()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{file_path:path}")
async def get_progress(file_path: str) -> Dict[str, Any]:
    """
    获取指定文件的上传进度
    
    Args:
        file_path: 文件路径
        
    Returns:
        {
            "file_name": "video.mp4",
            "status": "uploading",
            "percentage": 45.5,
            ...
        }
    """
    try:
        progress_mgr = get_progress_manager()
        progress = await progress_mgr.get_progress(file_path)
        
        if not progress:
            raise HTTPException(status_code=404, detail="上传任务不存在")
        
        return progress.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_upload_sessions() -> Dict[str, Any]:
    """
    获取所有断点续传会话
    
    Returns:
        {
            "sessions": [
                {
                    "session_id": "abc123",
                    "file_path": "/path/to/file",
                    "file_size": 1024000,
                    "progress": 45.5,
                    "uploaded_parts": [1, 2, 3],
                    "total_parts": 10,
                    ...
                }
            ]
        }
    """
    try:
        resume_mgr = get_resume_manager()
        sessions = await resume_mgr.list_sessions()
        
        return {
            "sessions": [
                {
                    **session.to_dict(),
                    "progress": session.get_progress(),
                }
                for session in sessions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> Dict[str, Any]:
    """
    删除断点续传会话
    
    Args:
        session_id: 会话ID
        
    Returns:
        {"message": "会话已删除"}
    """
    try:
        resume_mgr = get_resume_manager()
        await resume_mgr.delete_session(session_id)
        
        return {"message": "会话已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/cleanup")
async def cleanup_expired_sessions(days: int = 7) -> Dict[str, Any]:
    """
    清理过期的断点续传会话
    
    Args:
        days: 超过多少天未更新的会话将被清理（默认7天）
        
    Returns:
        {"message": "已清理过期会话"}
    """
    try:
        resume_mgr = get_resume_manager()
        await resume_mgr.clean_expired_sessions(days)
        
        return {"message": f"已清理超过{days}天未更新的会话"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

