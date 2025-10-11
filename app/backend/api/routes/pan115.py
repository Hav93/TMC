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
        
        # 检查是否已配置（脱敏显示）
        is_configured = bool(
            getattr(settings, 'pan115_app_id', None) and
            getattr(settings, 'pan115_user_id', None)
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
                from services.p115_service import P115Service
                p115 = P115Service(cookies=settings.pan115_user_key)
                user_info = await p115.get_user_info(settings.pan115_user_key)
                if user_info:
                    result['user_info'] = user_info
                    logger.info(f"✅ 获取到用户信息: {user_info.get('user_name', 'N/A')}")
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
    """测试115网盘连接（使用p115client SDK）"""
    try:
        from services.p115_service import get_p115_service
        
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            raise HTTPException(status_code=400, detail="未配置115网盘")
        
        user_id = getattr(settings, 'pan115_user_id', None)
        cookies = getattr(settings, 'pan115_user_key', None)
        
        if not user_id or not cookies:
            raise HTTPException(status_code=400, detail="请先登录115网盘")
        
        # 使用p115client测试连接
        p115 = get_p115_service(cookies=cookies)
        
        if p115.is_logged_in():
            # 测试列出根目录（作为连接测试）
            list_result = await p115.list_files(parent_id="0")
            
            if list_result.get('success'):
                return {
                    "success": True,
                    "message": "连接成功",
                    "user_id": user_id,
                    "files_count": len(list_result.get('files', [])),
                    "folders_count": len(list_result.get('folders', []))
                }
            else:
                raise HTTPException(status_code=400, detail="连接失败")
        else:
            raise HTTPException(status_code=400, detail="115网盘未登录")
            
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
    """上传文件到115网盘"""
    try:
        from services.p115_service import get_p115_service
        from pathlib import Path
        
        # 检查文件是否存在
        if not Path(file_path).exists():
            raise HTTPException(status_code=400, detail=f"文件不存在: {file_path}")
        
        # 获取115登录信息
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            raise HTTPException(status_code=400, detail="未配置115网盘")
        
        cookies = getattr(settings, 'pan115_user_key', None)
        
        if not cookies:
            raise HTTPException(status_code=400, detail="请先登录115网盘")
        
        # 使用p115client上传
        p115 = get_p115_service(cookies=cookies)
        upload_result = await p115.upload_file(
            file_path=file_path,
            remote_path=remote_path
        )
        
        if upload_result.get('success'):
            logger.info(f"✅ 文件上传成功: {upload_result['file_name']}")
            return upload_result
        else:
            raise HTTPException(status_code=400, detail=upload_result.get('message', '上传失败'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 上传文件异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class RegularQRCodeRequest(BaseModel):
    """常规115登录二维码请求"""
    device_type: str = "qandroid"  # 设备类型：qandroid/qios/android/ios/ipad/web/harmony/alipaymini/wechatmini


@router.post("/regular-qrcode")
async def get_regular_qrcode(
    request: RegularQRCodeRequest,
    current_user: User = Depends(get_current_user)
):
    """获取常规115登录二维码（使用p115client SDK）"""
    try:
        from services.p115_service import P115Service
        
        logger.info(f"📱 获取常规115登录二维码: 设备类型={request.device_type}")
        
        # 使用p115client获取二维码，传入设备类型
        p115 = P115Service()
        result = await p115.qrcode_login(device_type=request.device_type)
        
        if result.get('success'):
            logger.info(f"✅ 二维码获取成功: token={result['qrcode_token']}, device={request.device_type}")
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
    """检查常规115登录二维码状态（使用p115client SDK）"""
    try:
        qrcode_token_data = request.get('qrcode_token_data')
        device_type = request.get('device_type', 'qandroid')
        
        if not qrcode_token_data:
            raise HTTPException(status_code=400, detail="缺少qrcode_token_data参数")
        
        from services.p115_service import P115Service
        
        logger.info(f"🔍 检查常规115登录二维码状态: uid={qrcode_token_data.get('uid')}, device={device_type}")
        
        # 使用p115client检查状态
        p115 = P115Service()
        result = await p115.check_qrcode_status(qrcode_token_data, device_type)
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', '检查状态失败'))
        
        # 如果登录成功，保存cookies到数据库
        if result.get('status') == 'confirmed':
            cookies = result.get('cookies')
            user_id = result.get('user_id')
            user_info = result.get('user_info', {})  # 获取完整的用户信息
            
            if cookies and user_id:
                # 保存到数据库
                db_result = await db.execute(select(MediaSettings))
                settings = db_result.scalars().first()
                if not settings:
                    settings = MediaSettings()
                    db.add(settings)
                
                # 存储完整的cookies字符串、用户信息和设备类型
                setattr(settings, 'pan115_user_id', user_id)
                setattr(settings, 'pan115_user_key', cookies)
                setattr(settings, 'pan115_device_type', device_type)
                await db.commit()
                
                logger.info(f"✅ 115登录成功并已保存: UID={user_id}, 用户名={user_info.get('user_name', 'N/A')}")
                
                # 在返回结果中添加用户信息用于前端显示
                result['user_info'] = user_info
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 检查常规115登录二维码状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

