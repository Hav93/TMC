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

# CloudDrive2 客户端缓存（避免每次都重新获取token）
_clouddrive_clients: Dict[str, Any] = {}


def get_cached_clouddrive_client(url: str, username: str, password: str):
    """获取缓存的CloudDrive客户端，避免重复获取token"""
    from services.clouddrive2_client import CloudDrive2Client
    
    # 使用 URL + 用户名 作为缓存key（密码不放在key中，防止日志泄露）
    cache_key = f"{url}::{username}"
    
    # 如果缓存中没有，或者密码变了，创建新客户端
    if cache_key not in _clouddrive_clients:
        logger.info(f"🆕 创建新的 CloudDrive2 客户端: {url}")
        _clouddrive_clients[cache_key] = CloudDrive2Client(
            url=url,
            username=username,
            password=password
        )
    else:
        # 检查密码是否变化（简单比较）
        existing_client = _clouddrive_clients[cache_key]
        if existing_client.password != password:
            logger.info(f"🔄 密码已变更，重新创建 CloudDrive2 客户端: {url}")
            _clouddrive_clients[cache_key] = CloudDrive2Client(
                url=url,
                username=username,
                password=password
            )
    
    return _clouddrive_clients[cache_key]


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


@router.post("/test-clouddrive")
async def test_clouddrive_connection(
    data: MediaSettingsSchema,
    current_user: User = Depends(get_current_user)
):
    """测试 CloudDrive2 连接（使用gRPC-Web协议）"""
    try:
        if not data.clouddrive_url:
            raise HTTPException(status_code=400, detail="CloudDrive 服务地址不能为空")
        
        logger.info(f"🔗 测试 CloudDrive2 连接: {data.clouddrive_url}")
        
        # 使用缓存的 CloudDrive2Client（避免重复获取token）
        client = get_cached_clouddrive_client(
            url=data.clouddrive_url,
            username=data.clouddrive_username or "",
            password=data.clouddrive_password or ""
        )
        
        # 尝试获取 token 来验证连接
        try:
            token = await client.get_token()
            if token:
                logger.info("✅ CloudDrive2 连接成功，已获取认证令牌")
                
                # 尝试列出根目录来进一步验证
                try:
                    files = await client.list_files("/")
                    logger.info(f"✅ 成功列出根目录，共 {len(files)} 个文件/文件夹")
                    return {
                        "success": True,
                        "message": f"CloudDrive2 连接测试成功，根目录有 {len(files)} 个项目"
                    }
                except Exception as e:
                    logger.warning(f"⚠️ 获取目录列表失败: {e}")
                    return {
                        "success": True,
                        "message": "CloudDrive2 认证成功，但无法列出目录（可能是权限问题）"
                    }
            else:
                logger.error("❌ CloudDrive2 认证失败，未获取到令牌")
                return {
                    "success": False,
                    "message": "认证失败，请检查用户名和密码"
                }
        except Exception as auth_error:
            logger.error(f"❌ CloudDrive2 认证失败: {auth_error}")
            return {
                "success": False,
                "message": f"认证失败: {str(auth_error)}"
            }
            
    except Exception as e:
        logger.error(f"CloudDrive2 连接测试失败: {e}")
        return {
            "success": False,
            "message": f"连接失败: {str(e)}"
        }


@router.post("/clouddrive/browse")
async def browse_clouddrive_directory(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """浏览 CloudDrive2 目录（使用gRPC-Web协议）"""
    try:
        url = data.get("clouddrive_url")
        username = data.get("clouddrive_username")
        password = data.get("clouddrive_password")
        path = data.get("path", "/")
        
        if not url:
            raise HTTPException(status_code=400, detail="CloudDrive 服务地址不能为空")
        
        logger.info(f"📂 浏览 CloudDrive2 目录: {path}")
        
        # 使用缓存的 CloudDrive2Client（避免重复获取token）
        client = get_cached_clouddrive_client(
            url=url,
            username=username or "",
            password=password or ""
        )
        
        # 获取目录列表
        try:
            result = await client.list_files(path)
            
            # 调试日志
            logger.info(f"📊 list_files 返回类型: {type(result)}")
            logger.info(f"📊 list_files 返回内容: {str(result)[:500]}")
            
            # list_files 返回的是字典 {"success": bool, "directories": [], "files": []}
            if isinstance(result, dict):
                if result.get("success"):
                    directories = result.get("directories", [])
                    files = result.get("files", [])
                    
                    # 如果有 files 字段，需要过滤出目录
                    if files and not directories:
                        directories = [
                            {
                                "name": f.get("name"),
                                "path": f.get("path"),
                                "size": f.get("size", 0),
                                "modified": f.get("modifiedTime")
                            }
                            for f in files
                            if isinstance(f, dict) and f.get("isDirectory", False)
                        ]
                    
                    logger.info(f"✅ 找到 {len(directories)} 个目录")
                    return {
                        "success": True,
                        "directories": directories,
                        "current_path": path,
                        "message": result.get("message", "成功")
                    }
                else:
                    logger.warning(f"⚠️ CloudDrive2 返回失败: {result.get('message')}")
                    return {
                        "success": False,
                        "message": result.get("message", "未知错误"),
                        "directories": []
                    }
            else:
                logger.error(f"❌ 意外的返回类型: {type(result)}")
                return {
                    "success": False,
                    "message": f"意外的返回类型: {type(result)}",
                    "directories": []
                }
        except Exception as e:
            logger.error(f"❌ 获取目录列表失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"获取目录列表失败: {str(e)}",
                "directories": []
            }
    except Exception as e:
        logger.error(f"CloudDrive2 目录浏览失败: {e}")
        return {
            "success": False,
            "message": f"浏览失败: {str(e)}",
            "directories": []
        }


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

