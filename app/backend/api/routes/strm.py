"""
STRM文件生成API路由
"""
from fastapi import APIRouter, Depends
from typing import Optional, Any
from pydantic import BaseModel, Field

from api.dependencies import get_current_user
from services.strm_generator import generate_strm_file, StrmConfig, get_strm_generator
from log_manager import get_logger

logger = get_logger('strm_api', 'enhanced_bot.log')

router = APIRouter(tags=["STRM生成"])


class GenerateStrmRequest(BaseModel):
    """生成STRM请求"""
    media_url: str = Field(..., description="媒体URL")
    output_dir: str = Field(..., description="输出目录")
    filename: str = Field(..., description="文件名（不含扩展名）")
    title: Optional[str] = Field(None, description="标题")
    year: Optional[int] = Field(None, description="年份")
    plot: Optional[str] = Field(None, description="简介")
    genre: Optional[str] = Field(None, description="类型")
    rating: Optional[float] = Field(None, description="评分")
    include_nfo: bool = Field(True, description="是否生成NFO")
    nfo_type: str = Field("movie", description="NFO类型（movie/tvshow）")


@router.post("/generate")
async def generate_strm(
    request: GenerateStrmRequest,
    current_user: Any = Depends(get_current_user)
):
    """生成STRM文件"""
    try:
        config = StrmConfig(
            media_url=request.media_url,
            output_dir=request.output_dir,
            filename=request.filename,
            title=request.title,
            year=request.year,
            plot=request.plot,
            genre=request.genre,
            rating=request.rating
        )
        
        generator = get_strm_generator()
        result = generator.generate_complete(
            config,
            include_nfo=request.include_nfo,
            nfo_type=request.nfo_type
        )
        
        return {
            "success": True,
            "message": "STRM文件生成成功",
            "data": result
        }
    except Exception as e:
        logger.error(f"生成STRM失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.post("/generate-simple")
async def generate_strm_simple(
    media_url: str,
    output_dir: str,
    filename: str,
    current_user: Any = Depends(get_current_user)
):
    """简单生成STRM文件"""
    try:
        result = generate_strm_file(media_url, output_dir, filename)
        
        return {
            "success": True,
            "message": "STRM文件生成成功",
            "data": result
        }
    except Exception as e:
        logger.error(f"生成STRM失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}

