"""
秒传检测API路由
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Any

from api.dependencies import get_current_user
from services.quick_upload_service import get_quick_upload_service, calculate_file_sha1
from log_manager import get_logger

logger = get_logger('quick_upload_api', 'enhanced_bot.log')

router = APIRouter(tags=["秒传检测"])


class SHA1Request(BaseModel):
    """SHA1计算请求"""
    file_path: str = Field(..., description="文件路径")


class QuickCheckRequest(BaseModel):
    """秒传检测请求"""
    file_path: str = Field(..., description="文件路径")


@router.post("/sha1")
async def calculate_sha1(
    request: SHA1Request,
    current_user: Any = Depends(get_current_user)
):
    """计算文件SHA1"""
    try:
        sha1_hash = calculate_file_sha1(request.file_path)
        
        if sha1_hash:
            return {
                "success": True,
                "data": {
                    "file_path": request.file_path,
                    "sha1": sha1_hash
                }
            }
        else:
            return {
                "success": False,
                "message": "SHA1计算失败"
            }
            
    except Exception as e:
        logger.error(f"SHA1计算失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.post("/check")
async def check_quick(
    request: QuickCheckRequest,
    current_user: Any = Depends(get_current_user)
):
    """检查文件秒传"""
    try:
        service = get_quick_upload_service()
        result = await service.check_quick_upload(request.file_path)
        
        return {
            "success": True,
            "data": {
                "file_path": result.file_path,
                "file_size": result.file_size,
                "sha1": result.sha1_hash,
                "is_quick": result.is_quick,
                "check_time": result.check_time,
                "error": result.error
            }
        }
        
    except Exception as e:
        logger.error(f"秒传检测失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.get("/stats")
async def get_stats(current_user: Any = Depends(get_current_user)):
    """获取秒传统计"""
    try:
        service = get_quick_upload_service()
        stats = service.get_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"获取统计失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}

