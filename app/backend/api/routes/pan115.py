"""
115网盘配置和登录API
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from pydantic import BaseModel

from database import get_db
from models import User, MediaSettings
from api.dependencies import get_current_user
from services.pan115_client import Pan115Client
from log_manager import get_logger

logger = get_logger('pan115_api')

router = APIRouter(tags=["115网盘"])


class Pan115ConfigUpdate(BaseModel):
    """115网盘配置更新"""
    pan115_app_id: Optional[str] = None
    pan115_user_id: Optional[str] = None  # 手动输入的user_id
    pan115_user_key: Optional[str] = None  # 手动输入的user_key
    pan115_request_interval: Optional[float] = 1.0  # API请求间隔（秒）
    pan115_device_type: Optional[str] = None  # 登录设备类型


class Pan115QRCodeRequest(BaseModel):
    """115网盘扫码登录请求"""
    app_id: str


@router.get("/config")
async def get_pan115_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取115网盘配置"""
    try:
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            return {
                "pan115_app_id": None,
                "pan115_user_id": None,
                "pan115_user_key": None,
                "pan115_request_interval": 1.0,
                "is_configured": False
            }
        
        # 检查是否已配置：只要有user_id和user_key就算配置完成
        is_configured = bool(
            getattr(settings, 'pan115_user_id', None) and
            getattr(settings, 'pan115_user_key', None)
        )
        
        user_key_masked = None
        
        if hasattr(settings, 'pan115_user_key') and settings.pan115_user_key:
            user_key_masked = settings.pan115_user_key[:4] + '****' + settings.pan115_user_key[-4:] if len(settings.pan115_user_key) > 8 else '****'
        
        result = {
            "pan115_app_id": getattr(settings, 'pan115_app_id', None),
            "pan115_user_id": getattr(settings, 'pan115_user_id', None),
            "pan115_user_key": user_key_masked,
            "pan115_request_interval": getattr(settings, 'pan115_request_interval', 1.0),
            "pan115_device_type": getattr(settings, 'pan115_device_type', 'qandroid'),
            "is_configured": is_configured
        }
        
        # 如果已登录，尝试获取用户详细信息
        if is_configured and hasattr(settings, 'pan115_user_key') and settings.pan115_user_key:
            try:
                # 使用 Pan115Client 获取用户信息
                app_id = getattr(settings, 'pan115_app_id', None) or ""
                user_id = getattr(settings, 'pan115_user_id', None) or ""
                user_key = settings.pan115_user_key
                
                client = Pan115Client(
                    app_id=app_id,
                    app_key="",
                    user_id=user_id,
                    user_key=user_key
                )
                
                user_info_result = await client.get_user_info()
                if user_info_result.get('success') and 'user_info' in user_info_result:
                    result['user_info'] = user_info_result['user_info']
                    logger.info(f"✅ 获取到用户信息: {user_info_result['user_info'].get('user_name', 'N/A')}")
            except Exception as e:
                logger.warning(f"⚠️ 获取用户信息失败: {e}")
        
        logger.info(f"📤 返回115配置: {result}")
        return result
        
    except Exception as e:
        logger.error(f"获取115网盘配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def update_pan115_config(
    config: Pan115ConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新115网盘配置"""
    try:
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            # 创建默认配置
            settings = MediaSettings()
            db.add(settings)
        
        # 更新配置（使用setattr以支持动态字段）
        if config.pan115_app_id is not None:
            setattr(settings, 'pan115_app_id', config.pan115_app_id)
        
        if config.pan115_user_id is not None:
            setattr(settings, 'pan115_user_id', config.pan115_user_id)
        
        if config.pan115_user_key is not None:
            setattr(settings, 'pan115_user_key', config.pan115_user_key)
        
        if config.pan115_request_interval is not None:
            setattr(settings, 'pan115_request_interval', config.pan115_request_interval)
        
        if config.pan115_device_type is not None:
            setattr(settings, 'pan115_device_type', config.pan115_device_type)
        
        await db.commit()
        
        logger.info(f"✅ 115网盘配置已更新: app_id={config.pan115_app_id}, user_id={config.pan115_user_id if config.pan115_user_id else '未设置'}")
        
        return {
            "success": True,
            "message": "115网盘配置已更新"
        }
        
    except Exception as e:
        logger.error(f"更新115网盘配置失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qrcode")
async def get_qrcode_for_login(
    request: Pan115QRCodeRequest,
    current_user: User = Depends(get_current_user)
):
    """获取115登录二维码"""
    try:
        logger.info(f"📥 收到二维码请求: app_id={request.app_id}")
        
        # 创建临时客户端（只需要app_id）
        client = Pan115Client(
            app_id=request.app_id,
            app_key="",  # 不需要app_key
            user_id="",  # 登录前没有user_id
            user_key=""  # 登录前没有user_key
        )
        
        # 获取二维码
        result = await client.get_qrcode_token()
        
        if result['success']:
            logger.info(f"✅ 115二维码获取成功: token={result['qrcode_token']}")
            return {
                "success": True,
                "qrcode_token": result['qrcode_token'],
                "qrcode_url": result['qrcode_url'],
                "expires_in": result['expires_in']
            }
        else:
            logger.error(f"❌ 115二维码获取失败: {result.get('message')}")
            raise HTTPException(status_code=400, detail=result.get('message', '获取二维码失败'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取115二维码异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qrcode/status")
async def check_qrcode_login_status(
    data: Dict[str, str] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查115二维码扫码状态"""
    try:
        qrcode_token = data.get('qrcode_token')
        app_id = data.get('app_id')
        
        if not all([qrcode_token, app_id]):
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 创建临时客户端
        client = Pan115Client(
            app_id=app_id,
            app_key="",  # 不需要app_key
            user_id="",
            user_key=""
        )
        
        # 检查扫码状态
        result = await client.check_qrcode_status(qrcode_token)
        
        if not result['success']:
            return {
                "success": False,
                "status": result.get('status', 'error'),
                "message": result.get('message', '检查状态失败')
            }
        
        status = result['status']
        
        # 如果已确认登录，保存用户凭据
        if status == 'confirmed':
            user_id = result.get('user_id')
            user_key = result.get('user_key')
            
            if user_id and user_key:
                # 保存到数据库
                settings_result = await db.execute(select(MediaSettings))
                settings = settings_result.scalars().first()
                
                if not settings:
                    settings = MediaSettings()
                    db.add(settings)
                
                settings.pan115_user_id = user_id
                settings.pan115_user_key = user_key
                
                await db.commit()
                
                logger.info(f"✅ 115用户登录成功并保存: user_id={user_id}")
                
                return {
                    "success": True,
                    "status": "confirmed",
                    "user_id": user_id,
                    "message": "登录成功"
                }
        
        return {
            "success": True,
            "status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查115扫码状态异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_pan115_connection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试115网盘连接（使用 Pan115Client）"""
    try:
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            raise HTTPException(status_code=400, detail="未配置115网盘")
        
        app_id = getattr(settings, 'pan115_app_id', None)
        user_id = getattr(settings, 'pan115_user_id', None)
        user_key = getattr(settings, 'pan115_user_key', None)
        
        if not all([app_id, user_id, user_key]):
            raise HTTPException(status_code=400, detail="请先配置并登录115网盘")
        
        # 使用 Pan115Client 测试连接
        client = Pan115Client(
            app_id=app_id,
            app_key="",  # Open API 可能不需要 app_key
            user_id=user_id,
            user_key=user_key
        )
        
        test_result = await client.test_connection()
        
        if test_result.get('success'):
            return {
                "success": True,
                "message": test_result.get('message', '连接成功'),
                "user_id": user_id,
                "user_info": test_result.get('user_info', {})
            }
        else:
            raise HTTPException(status_code=400, detail=test_result.get('message', '连接失败'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试115连接异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_to_pan115(
    file_path: str = Body(...),
    remote_path: str = Body(default="/telegram_downloads"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文件到115网盘（使用 Pan115Client）"""
    try:
        from pathlib import Path
        
        # 检查文件是否存在
        if not Path(file_path).exists():
            raise HTTPException(status_code=400, detail=f"文件不存在: {file_path}")
        
        # 获取115登录信息
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            raise HTTPException(status_code=400, detail="未配置115网盘")
        
        app_id = getattr(settings, 'pan115_app_id', None)
        user_id = getattr(settings, 'pan115_user_id', None)
        user_key = getattr(settings, 'pan115_user_key', None)
        
        if not all([app_id, user_id, user_key]):
            raise HTTPException(status_code=400, detail="请先配置并登录115网盘")
        
        # 使用 Pan115Client 上传
        client = Pan115Client(
            app_id=app_id,
            app_key="",
            user_id=user_id,
            user_key=user_key
        )
        
        upload_result = await client.upload_file(
            file_path=file_path,
            target_path=remote_path
        )
        
        if upload_result.get('success'):
            logger.info(f"✅ 文件上传成功: {Path(file_path).name}")
            return {
                "success": True,
                "file_id": upload_result.get('file_id', ''),
                "file_name": Path(file_path).name,
                "is_quick": upload_result.get('quick_upload', False),
                "message": upload_result.get('message', '上传成功')
            }
        else:
            raise HTTPException(status_code=400, detail=upload_result.get('message', '上传失败'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 上传文件异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 常规扫码登录（非 Open API）====================

class RegularQRCodeRequest(BaseModel):
    """常规115登录二维码请求"""
    app: str = "web"  # 应用类型：web/android/ios/tv/alipaymini/wechatmini/qandroid


@router.post("/regular-qrcode")
async def get_regular_qrcode(
    request: RegularQRCodeRequest,
    current_user: User = Depends(get_current_user)
):
    """获取常规115登录二维码（使用 Pan115Client）"""
    try:
        logger.info(f"📱 获取常规115登录二维码: app={request.app}")
        
        # 使用 Pan115Client 的静态方法获取二维码
        result = await Pan115Client.get_regular_qrcode(app=request.app)
        
        if result.get('success'):
            logger.info(f"✅ 二维码获取成功: token={result['qrcode_token'].get('uid')}, app={request.app}")
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('message', '获取二维码失败'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取常规115登录二维码失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regular-qrcode/status")
async def check_regular_qrcode_status(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查常规115登录二维码状态（使用 Pan115Client）"""
    try:
        # 添加详细的请求日志
        logger.info(f"📥 收到二维码状态检查请求: {request}")
        
        qrcode_token = request.get('qrcode_token')
        app = request.get('app', 'web')
        
        logger.info(f"📦 解析参数: qrcode_token={qrcode_token}, app={app}")
        
        if not qrcode_token:
            logger.error("❌ 缺少qrcode_token参数")
            raise HTTPException(status_code=400, detail="缺少qrcode_token参数")
        
        logger.info(f"🔍 检查常规115登录二维码状态: uid={qrcode_token.get('uid') if isinstance(qrcode_token, dict) else 'N/A'}, app={app}")
        
        # 使用 Pan115Client 的静态方法检查状态
        result = await Pan115Client.check_regular_qrcode_status(qrcode_token, app)
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', '检查状态失败'))
        
        # 如果登录成功，保存cookies到数据库
        if result.get('status') == 'confirmed':
            cookies = result.get('cookies')
            user_id = result.get('user_id')
            user_info = result.get('user_info', {})
            
            if cookies and user_id:
                # 保存到数据库
                db_result = await db.execute(select(MediaSettings))
                settings = db_result.scalars().first()
                if not settings:
                    settings = MediaSettings()
                    db.add(settings)
                
                # 常规登录存储 cookies
                # 注意：这里存储的是 cookies，不是 Open API 的 user_key
                setattr(settings, 'pan115_user_id', user_id)
                setattr(settings, 'pan115_user_key', cookies)  # 复用字段存储 cookies
                setattr(settings, 'pan115_device_type', app)
                await db.commit()
                
                logger.info(f"✅ 115常规登录成功并已保存: UID={user_id}, 用户名={user_info.get('user_name', 'N/A')}")
                
                # 在返回结果中添加用户信息用于前端显示
                result['user_info'] = user_info
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 检查常规115登录二维码状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

