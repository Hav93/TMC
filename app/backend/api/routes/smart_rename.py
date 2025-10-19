"""
智能重命名API路由
"""
from fastapi import APIRouter, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from api.dependencies import get_current_user
from services.smart_rename_service import get_smart_rename_service, smart_rename, parse_media_filename
from log_manager import get_logger

logger = get_logger('smart_rename_api', 'enhanced_bot.log')

router = APIRouter(tags=["智能重命名"])


class ParseRequest(BaseModel):
    """解析请求"""
    filename: str = Field(..., description="文件名")


class RenameRequest(BaseModel):
    """重命名请求"""
    filename: str = Field(..., description="原文件名")
    template: Optional[str] = Field(None, description="自定义模板")


class BatchRenameRequest(BaseModel):
    """批量重命名请求"""
    filenames: List[str] = Field(..., description="文件名列表")
    template: Optional[str] = Field(None, description="自定义模板")


@router.post("/parse")
async def parse_filename(
    request: ParseRequest,
    current_user: Any = Depends(get_current_user)
):
    """解析文件名，提取元数据"""
    try:
        metadata = parse_media_filename(request.filename)
        
        return {
            "success": True,
            "data": {
                "media_type": metadata.media_type.value,
                "title": metadata.title,
                "year": metadata.year,
                "season": metadata.season,
                "episode": metadata.episode,
                "resolution": metadata.resolution,
                "codec": metadata.codec,
                "audio": metadata.audio,
                "source": metadata.source,
                "extension": metadata.extension
            }
        }
    except Exception as e:
        logger.error(f"解析文件名失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.post("/rename")
async def rename_file(
    request: RenameRequest,
    current_user: Any = Depends(get_current_user)
):
    """智能重命名单个文件"""
    try:
        new_filename = smart_rename(request.filename, request.template)
        
        return {
            "success": True,
            "data": {
                "original": request.filename,
                "renamed": new_filename
            }
        }
    except Exception as e:
        logger.error(f"重命名失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.post("/batch-rename")
async def batch_rename_files(
    request: BatchRenameRequest,
    current_user: Any = Depends(get_current_user)
):
    """批量重命名文件"""
    try:
        service = get_smart_rename_service()
        result = service.batch_rename(request.filenames, request.template)
        
        return {
            "success": True,
            "data": {
                "total": len(request.filenames),
                "renamed": result
            }
        }
    except Exception as e:
        logger.error(f"批量重命名失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.get("/templates")
async def get_templates(current_user: Any = Depends(get_current_user)):
    """获取命名模板"""
    templates = {
        "movie": "{title}.({year}).{resolution}.{source}.{codec}.{ext}",
        "tv": "{title}.S{season}E{episode}.{resolution}.{source}.{codec}.{ext}",
        "simple": "{title}.{resolution}.{ext}",
        "detailed": "{title}.{year}.{resolution}.{source}.{codec}.{audio}.{ext}"
    }
    
    return {
        "success": True,
        "data": templates
    }

