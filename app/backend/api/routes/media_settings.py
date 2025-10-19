"""
媒体管理全局配置 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from database import get_db
from models import MediaSettings, User
from auth import get_current_user
from log_manager import get_logger
import httpx
import os
from pathlib import Path

logger = get_logger('api.media_settings')
router = APIRouter()


class MediaSettingsSchema(BaseModel):
    """媒体配置Schema"""
    # 下载设置
    temp_folder: str = "/app/media/downloads"
    concurrent_downloads: int = 3
    retry_on_failure: bool = True
    max_retries: int = 3
    
    # 元数据提取
    extract_metadata: bool = True
    metadata_mode: str = "lightweight"
    metadata_timeout: int = 10
    async_metadata_extraction: bool = True
    
    # 存储清理
    auto_cleanup_enabled: bool = True
    auto_cleanup_days: int = 7
    cleanup_only_organized: bool = True
    max_storage_gb: int = 100


@router.get("/")
async def get_media_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取媒体管理全局配置"""
    try:
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            # 如果没有配置，创建默认配置
            settings = MediaSettings(
                temp_folder="/app/media/downloads",
                concurrent_downloads=3,
                retry_on_failure=True,
                max_retries=3,
                extract_metadata=True,
                metadata_mode="lightweight",
                metadata_timeout=10,
                async_metadata_extraction=True,
                auto_cleanup_enabled=True,
                auto_cleanup_days=7,
                cleanup_only_organized=True,
                max_storage_gb=100
            )
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
            logger.info("📝 创建默认媒体配置")
        
        return {
            "id": settings.id,
            "temp_folder": settings.temp_folder,
            "concurrent_downloads": settings.concurrent_downloads,
            "retry_on_failure": settings.retry_on_failure,
            "max_retries": settings.max_retries,
            "extract_metadata": settings.extract_metadata,
            "metadata_mode": settings.metadata_mode,
            "metadata_timeout": settings.metadata_timeout,
            "async_metadata_extraction": settings.async_metadata_extraction,
            "auto_cleanup_enabled": settings.auto_cleanup_enabled,
            "auto_cleanup_days": settings.auto_cleanup_days,
            "cleanup_only_organized": settings.cleanup_only_organized,
            "max_storage_gb": settings.max_storage_gb,
            "created_at": settings.created_at.isoformat() if settings.created_at else None,
            "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
        }
    except Exception as e:
        logger.error(f"获取媒体配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/")
async def update_media_settings(
    data: MediaSettingsSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新媒体管理全局配置"""
    try:
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            # 如果没有配置，创建新的
            settings = MediaSettings()
            db.add(settings)
        
        # 更新所有字段
        settings.temp_folder = data.temp_folder
        settings.concurrent_downloads = data.concurrent_downloads
        settings.retry_on_failure = data.retry_on_failure
        settings.max_retries = data.max_retries
        settings.extract_metadata = data.extract_metadata
        settings.metadata_mode = data.metadata_mode
        settings.metadata_timeout = data.metadata_timeout
        settings.async_metadata_extraction = data.async_metadata_extraction
        settings.auto_cleanup_enabled = data.auto_cleanup_enabled
        settings.auto_cleanup_days = data.auto_cleanup_days
        settings.cleanup_only_organized = data.cleanup_only_organized
        settings.max_storage_gb = data.max_storage_gb
        
        await db.commit()
        await db.refresh(settings)
        
        logger.info(f"✅ 媒体配置已更新 (ID: {settings.id})")
        
        return {"message": "配置更新成功", "id": settings.id}
    except Exception as e:
        logger.error(f"更新媒体配置失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/local-directories")
async def get_local_directories(
    path: str = "/app",
    current_user: User = Depends(get_current_user)
):
    """获取本地目录列表"""
    try:
        logger.info(f"📂 浏览本地目录: {path}")
        
        target_path = Path(path)
        
        # 安全检查：只允许浏览特定目录
        allowed_roots = ["/app", "/app/media", "/data", "/mnt"]
        is_allowed = False
        for root in allowed_roots:
            try:
                target_path.resolve().relative_to(Path(root).resolve())
                is_allowed = True
                break
            except ValueError:
                continue
        
        if not is_allowed:
            raise HTTPException(status_code=403, detail="不允许访问此目录")
        
        # 如果目录不存在，尝试返回父目录
        if not target_path.exists():
            logger.warning(f"⚠️ 目录不存在: {path}，尝试返回父目录")
            # 找到第一个存在的父目录
            current = target_path
            while current != current.parent:
                current = current.parent
                if current.exists() and current.is_dir():
                    logger.info(f"📂 返回父目录: {current}")
                    target_path = current
                    break
            else:
                # 如果所有父目录都不存在，返回允许的根目录
                for root in allowed_roots:
                    root_path = Path(root)
                    if root_path.exists() and root_path.is_dir():
                        target_path = root_path
                        logger.info(f"📂 返回根目录: {root}")
                        break
                else:
                    raise HTTPException(status_code=404, detail="无可用目录")
        
        if not target_path.is_dir():
            raise HTTPException(status_code=400, detail="路径不是目录")
        
        # 获取子目录列表
        directories = []
        try:
            for item in sorted(target_path.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    try:
                        stat = item.stat()
                        directories.append({
                            "name": item.name,
                            "path": str(item),
                            "size": stat.st_size,
                            "modified": stat.st_mtime
                        })
                    except (PermissionError, OSError):
                        continue
        except PermissionError:
            raise HTTPException(status_code=403, detail="没有权限访问此目录")
        
        # 获取父目录路径
        parent_path = str(target_path.parent) if target_path.parent != target_path else None
        
        logger.info(f"✅ 找到 {len(directories)} 个子目录")
        return {
            "success": True,
            "directories": directories,
            "current_path": str(target_path),
            "parent_path": parent_path
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取本地目录列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class DirectoryOperationRequest(BaseModel):
    """目录操作请求"""
    path: str


class DirectoryRenameRequest(BaseModel):
    """目录重命名请求"""
    old_path: str
    new_path: str


@router.post("/local-directory/create")
async def create_local_directory(
    request: DirectoryOperationRequest,
    current_user: User = Depends(get_current_user)
):
    """创建本地目录"""
    try:
        logger.info(f"📁 创建目录: {request.path}")
        
        target_path = Path(request.path)
        
        # 安全检查：只允许在特定目录下创建
        allowed_roots = ["/app", "/app/media", "/data", "/mnt"]
        is_allowed = False
        for root in allowed_roots:
            try:
                target_path.resolve().relative_to(Path(root).resolve())
                is_allowed = True
                break
            except ValueError:
                continue
        
        if not is_allowed:
            raise HTTPException(status_code=403, detail="不允许在此位置创建目录")
        
        # 检查目录是否已存在
        if target_path.exists():
            return {
                "success": False,
                "message": "目录已存在"
            }
        
        # 创建目录
        target_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ 目录创建成功: {request.path}")
        
        return {
            "success": True,
            "message": "目录创建成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建目录失败: {e}")
        return {
            "success": False,
            "message": f"创建失败: {str(e)}"
        }


@router.post("/local-directory/rename")
async def rename_local_directory(
    request: DirectoryRenameRequest,
    current_user: User = Depends(get_current_user)
):
    """重命名本地目录"""
    try:
        logger.info(f"✏️ 重命名目录: {request.old_path} -> {request.new_path}")
        
        old_path = Path(request.old_path)
        new_path = Path(request.new_path)
        
        # 安全检查
        allowed_roots = ["/app", "/app/media", "/data", "/mnt"]
        for path in [old_path, new_path]:
            is_allowed = False
            for root in allowed_roots:
                try:
                    path.resolve().relative_to(Path(root).resolve())
                    is_allowed = True
                    break
                except ValueError:
                    continue
            
            if not is_allowed:
                raise HTTPException(status_code=403, detail="不允许操作此目录")
        
        # 检查源目录是否存在
        if not old_path.exists():
            return {
                "success": False,
                "message": "源目录不存在"
            }
        
        # 检查目标目录是否已存在
        if new_path.exists():
            return {
                "success": False,
                "message": "目标目录已存在"
            }
        
        # 重命名
        old_path.rename(new_path)
        logger.info(f"✅ 目录重命名成功: {request.old_path} -> {request.new_path}")
        
        return {
            "success": True,
            "message": "重命名成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重命名目录失败: {e}")
        return {
            "success": False,
            "message": f"重命名失败: {str(e)}"
        }


@router.post("/local-directory/delete")
async def delete_local_directory(
    request: DirectoryOperationRequest,
    current_user: User = Depends(get_current_user)
):
    """删除本地目录"""
    try:
        logger.info(f"🗑️ 删除目录: {request.path}")
        
        target_path = Path(request.path)
        
        # 安全检查
        allowed_roots = ["/app", "/app/media", "/data", "/mnt"]
        is_allowed = False
        for root in allowed_roots:
            try:
                target_path.resolve().relative_to(Path(root).resolve())
                is_allowed = True
                break
            except ValueError:
                continue
        
        if not is_allowed:
            raise HTTPException(status_code=403, detail="不允许删除此目录")
        
        # 额外保护：禁止删除系统关键目录
        protected_dirs = ["/app", "/app/media", "/data", "/mnt", "/app/sessions", "/app/logs"]
        if str(target_path) in protected_dirs:
            raise HTTPException(status_code=403, detail="不允许删除系统关键目录")
        
        # 检查目录是否存在
        if not target_path.exists():
            return {
                "success": False,
                "message": "目录不存在"
            }
        
        # 检查是否为空目录
        if any(target_path.iterdir()):
            return {
                "success": False,
                "message": "目录不为空，无法删除"
            }
        
        # 删除空目录
        target_path.rmdir()
        logger.info(f"✅ 目录删除成功: {request.path}")
        
        return {
            "success": True,
            "message": "删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除目录失败: {e}")
        return {
            "success": False,
            "message": f"删除失败: {str(e)}"
        }

