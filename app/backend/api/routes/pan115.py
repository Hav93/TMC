"""
115网盘配置和登录API
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import timedelta

from database import get_db
from models import User, MediaSettings
from api.dependencies import get_current_user
from services.pan115_client import Pan115Client
from log_manager import get_logger
from timezone_utils import get_user_now

logger = get_logger('pan115_api')

router = APIRouter(tags=["115网盘"])


def create_pan115_client(settings: MediaSettings, app_id: str = "", app_key: str = "", 
                         user_id: str = "", user_key: str = "") -> Pan115Client:
    """
    创建Pan115Client实例,自动读取use_proxy配置
    
    Args:
        settings: 媒体设置对象
        app_id: 应用ID (可�?会从settings读取)
        app_key: 应用密钥 (可�?
        user_id: 用户ID (可�?会从settings读取)
        user_key: 用户密钥 (可�?会从settings读取)
    """
    use_proxy = getattr(settings, 'pan115_use_proxy', False) or False
    
    # 如果没有提供app_key,从settings读取app_secret
    if not app_key:
        app_key = getattr(settings, 'pan115_app_secret', '') or ''
    
    return Pan115Client(
        app_id=app_id or getattr(settings, 'pan115_app_id', '') or '',
        app_key=app_key,
        user_id=user_id or getattr(settings, 'pan115_user_id', '') or '',
        user_key=user_key or getattr(settings, 'pan115_user_key', '') or '',
        use_proxy=use_proxy
    )


class Pan115ConfigUpdate(BaseModel):
    """115网盘配置更新"""
    pan115_app_id: Optional[str] = None
    pan115_app_secret: Optional[str] = None  # 115开放平台AppSecret
    pan115_user_id: Optional[str] = None  # 手动输入的user_id
    pan115_user_key: Optional[str] = None  # 手动输入的user_key
    pan115_request_interval: Optional[float] = 1.0  # API请求间隔（秒�?    pan115_device_type: Optional[str] = None  # 登录设备类型
    pan115_use_proxy: Optional[bool] = None  # 是否使用代理


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
        
        # 检查是否已激活开放平台API(有access_token且未过期)
        access_token = getattr(settings, 'pan115_access_token', None)
        token_expires_at = getattr(settings, 'pan115_token_expires_at', None)
        open_api_activated = False
        
        if access_token and token_expires_at:
            # 检查token是否未过�?            if token_expires_at > get_user_now():
                open_api_activated = True
                logger.info(f"�?开放平台API已激�?token有效期至: {token_expires_at}")
            else:
                logger.warning(f"⚠️ access_token已过�? {token_expires_at}")
        
        # AppSecret脱敏显示
        app_secret = getattr(settings, 'pan115_app_secret', None)
        app_secret_masked = None
        if app_secret:
            app_secret_masked = f"{app_secret[:4]}...{app_secret[-4:]}" if len(app_secret) > 8 else "***"
        
        result = {
            "pan115_app_id": getattr(settings, 'pan115_app_id', None),
            "pan115_app_secret": app_secret_masked,
            "pan115_user_id": getattr(settings, 'pan115_user_id', None),
            "pan115_user_key": user_key_masked,
            "pan115_request_interval": getattr(settings, 'pan115_request_interval', 1.0),
            "pan115_device_type": getattr(settings, 'pan115_device_type', 'qandroid'),
            "pan115_use_proxy": getattr(settings, 'pan115_use_proxy', False),
            "is_configured": is_configured,
            "open_api_activated": open_api_activated
        }
        
        # 如果已登录，尝试获取用户详细信息
        logger.info(f"🔎 检查条�? is_configured={is_configured}, has_attr={hasattr(settings, 'pan115_user_key')}, user_key_exists={bool(settings.pan115_user_key if hasattr(settings, 'pan115_user_key') else False)}")
        if is_configured and hasattr(settings, 'pan115_user_key') and settings.pan115_user_key:
            logger.info("�?条件满足，进入获取用户信息流�?)
            try:
                # 优先使用数据库中保存的用户信息（登录时保存的�?                if hasattr(settings, 'pan115_user_info') and settings.pan115_user_info:
                    try:
                        import json
                        cached_user_info = json.loads(settings.pan115_user_info)
                        result['user_info'] = cached_user_info
                        logger.info(f"�?使用缓存的用户信�? {cached_user_info.get('user_name', 'N/A')}, VIP={cached_user_info.get('vip_name', '普通用�?)}")
                    except Exception as parse_error:
                        logger.warning(f"⚠️ 解析缓存的用户信息失�? {parse_error}")
                        # 如果解析失败，继续尝试从API获取
                        pass
                
                # 如果没有缓存的用户信息，或解析失败，则从API获取
                if 'user_info' not in result:
                    app_id = getattr(settings, 'pan115_app_id', None) or ""
                    user_id = getattr(settings, 'pan115_user_id', None) or ""
                    user_key = settings.pan115_user_key
                    
                    logger.info(f"🔍 从API获取用户信息: user_id={user_id}")
                    
                    client = Pan115Client(
                        app_id=app_id,
                        app_key="",
                        user_id=user_id,
                        user_key=user_key
                    )
                    
                    user_info_result = await client.get_user_info()
                    
                    if user_info_result.get('success') and 'user_info' in user_info_result:
                        result['user_info'] = user_info_result['user_info']
                        logger.info(f"�?从API获取到用户信�?)
                        
                        # 更新数据库缓�?                        try:
                            import json
                            settings.pan115_user_info = json.dumps(user_info_result['user_info'], ensure_ascii=False)
                            await db.commit()
                            logger.info(f"💾 已更新用户信息缓�?)
                        except Exception as update_error:
                            logger.warning(f"⚠️ 更新用户信息缓存失败: {update_error}")
                    else:
                        logger.warning(f"⚠️ API获取用户信息失败: {user_info_result.get('message', 'N/A')}")
                        
            except Exception as e:
                logger.error(f"�?获取用户信息异常: {e}")
                import traceback
                traceback.print_exc()
        
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
        
        if config.pan115_app_secret is not None:
            setattr(settings, 'pan115_app_secret', config.pan115_app_secret)
        
        if config.pan115_user_id is not None:
            setattr(settings, 'pan115_user_id', config.pan115_user_id)
        
        if config.pan115_user_key is not None:
            setattr(settings, 'pan115_user_key', config.pan115_user_key)
        
        if config.pan115_request_interval is not None:
            setattr(settings, 'pan115_request_interval', config.pan115_request_interval)
        
        if config.pan115_device_type is not None:
            setattr(settings, 'pan115_device_type', config.pan115_device_type)
        
        if config.pan115_use_proxy is not None:
            setattr(settings, 'pan115_use_proxy', config.pan115_use_proxy)
        
        await db.commit()
        
        logger.info(f"�?115网盘配置已更�? app_id={config.pan115_app_id}, user_id={config.pan115_user_id if config.pan115_user_id else '未设�?}")
        
        return {
            "success": True,
            "message": "115网盘配置已更�?
        }
        
    except Exception as e:
        logger.error(f"更新115网盘配置失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-cookies")
async def test_cookies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    测试115 cookies的可用�?    读取持久化的cookies文件并验�?    """
    try:
        import os
        
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            raise HTTPException(status_code=400, detail="未找到配�?)
        
        user_id = getattr(settings, 'pan115_user_id', None)
        
        # 1. 先尝试从文件读取cookies
        cookies = None
        cookies_file = os.path.join('/app', 'config', '115-cookies.txt')
        
        if os.path.exists(cookies_file):
            try:
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    cookies = f.read().strip()
                logger.info(f"�?从文件读取cookies: {cookies_file}")
            except Exception as read_error:
                logger.warning(f"⚠️ 读取cookies文件失败: {read_error}")
        
        # 2. 如果文件不存�?从数据库读取
        if not cookies:
            cookies = getattr(settings, 'pan115_user_key', None)
            if cookies:
                logger.info(f"�?从数据库读取cookies")
        
        if not user_id or not cookies:
            raise HTTPException(status_code=400, detail="未找到cookies,请先扫码登录")
        
        logger.info(f"🧪 开始测试cookies可用�? user_id={user_id}")
        
        # 3. 使用cookies访问115 API验证
        client = Pan115Client(
            app_id="",
            app_key="",
            user_id=user_id,
            user_key=cookies
        )
        
        # 尝试获取用户信息来验证cookies
        user_info_result = await client.get_user_info()
        
        if user_info_result.get('success'):
            user_info = user_info_result.get('user_info', {})
            user_name = user_info.get('user_name', 'N/A')
            space = user_info.get('space', {})
            space_total = space.get('total', 0)
            space_used = space.get('used', 0)
            
            # 格式化空间信�?            def format_size(bytes_val):
                if bytes_val == 0:
                    return "0 B"
                units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
                i = 0
                size = float(bytes_val)
                while size >= 1024 and i < len(units) - 1:
                    size /= 1024
                    i += 1
                return f"{size:.2f}{units[i]}"
            
            logger.info(f"�?Cookies可用: {user_name}, 空间: {format_size(space_total)}")
            
            return {
                "success": True,
                "message": f"�?Cookies可用\n\n账号: {user_name}\n容量: {format_size(space_used)} / {format_size(space_total)}",
                "user_info": user_info
            }
        else:
            error_msg = user_info_result.get('message', '验证失败')
            logger.error(f"�?Cookies不可�? {error_msg}")
            raise HTTPException(status_code=400, detail=f"Cookies不可�? {error_msg}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"�?测试cookies异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/activate-open-api")
async def activate_open_api(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    激�?15开放平台API
    使用已保存的cookies + 配置的AppID获取access_token,并刷新用户信�?    """
    try:
        import os
        
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            raise HTTPException(status_code=400, detail="未找到配�?)
        
        app_id = getattr(settings, 'pan115_app_id', None)
        user_id = getattr(settings, 'pan115_user_id', None)
        
        if not app_id:
            raise HTTPException(status_code=400, detail="请先配置AppID")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="请先扫码登录115账号")
        
        # 1. 优先从文件读取cookies
        cookies = None
        cookies_file = os.path.join('/app', 'config', '115-cookies.txt')
        
        if os.path.exists(cookies_file):
            try:
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    cookies = f.read().strip()
                logger.info(f"�?从文件读取cookies: {cookies_file}")
            except Exception as read_error:
                logger.warning(f"⚠️ 读取cookies文件失败: {read_error}")
        
        # 2. 如果文件不存�?从数据库读取
        if not cookies:
            cookies = getattr(settings, 'pan115_user_key', None)
            if cookies:
                logger.info(f"�?从数据库读取cookies")
        
        if not cookies:
            raise HTTPException(status_code=400, detail="未找到cookies,请先扫码登录")
        
        # 读取代理配置
        use_proxy = getattr(settings, 'pan115_use_proxy', False)
        
        logger.info(f"🔑 开始激活开放平台API: app_id={app_id}, user_id={user_id}, use_proxy={use_proxy}")
        
        # 创建客户�?使用cookies)
        client = Pan115Client(
            app_id=app_id,
            app_key="",  # 不需要app_secret
            user_id=user_id,
            user_key=cookies,  # 使用cookies
            use_proxy=use_proxy  # 传递代理配�?        )
        
        # 直接使用已有的cookies + AppID获取access_token
        token_result = await client.get_access_token()
        
        if token_result.get('success'):
            access_token = token_result.get('access_token')
            refresh_token = token_result.get('refresh_token')
            expires_in = token_result.get('expires_in', 7200)
            
            # 保存access_token到数据库
            setattr(settings, 'pan115_access_token', access_token)
            if refresh_token:
                setattr(settings, 'pan115_refresh_token', refresh_token)
            setattr(settings, 'pan115_token_expires_at', get_user_now() + timedelta(seconds=expires_in))
            await db.commit()
            
            logger.info(f"�?access_token获取成功")
            
            # 尝试刷新用户信息
            client.access_token = access_token
            user_info_result = await client.get_user_info()
            
            if user_info_result.get('success') and 'user_info' in user_info_result:
                user_info = user_info_result['user_info']
                # 缓存用户信息
                import json
                setattr(settings, 'pan115_user_info', json.dumps(user_info, ensure_ascii=False))
                setattr(settings, 'pan115_last_refresh_at', get_user_now())
                await db.commit()
                
                logger.info(f"�?用户信息已刷�?)
                
                return {
                    "success": True,
                    "message": "�?开放平台API已激�?,
                    "user_info": user_info,
                    "has_space_info": user_info.get('space', {}).get('total', 0) > 0
                }
            else:
                return {
                    "success": True,
                    "message": "�?开放平台API已激活（用户信息将稍后刷新）",
                    "has_space_info": False
                }
        else:
            error_msg = token_result.get('message', '未知错误')
            logger.error(f"�?获取access_token失败: {error_msg}")
            raise HTTPException(status_code=400, detail=f"激活失�? {error_msg}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"�?激活开放平台API异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/poll-device-token")
async def poll_device_token(
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """轮询获取访问令牌(OAuth 2.0 Device Code Flow第二�?"""
    try:
        device_code = data.get('device_code')
        code_verifier = data.get('code_verifier')
        qrcode_token = data.get('qrcode_token')
        
        if not device_code or not code_verifier:
            raise HTTPException(status_code=400, detail="缺少device_code或code_verifier参数")
        
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            raise HTTPException(status_code=400, detail="未找到配�?)
        
        app_id = getattr(settings, 'pan115_app_id', None)
        user_id = getattr(settings, 'pan115_user_id', None)
        cookies = getattr(settings, 'pan115_user_key', None)
        use_proxy = getattr(settings, 'pan115_use_proxy', False)
        
        if not app_id:
            raise HTTPException(status_code=400, detail="请先配置AppID")
        
        # 创建客户�?        client = Pan115Client(
            app_id=app_id,
            app_key="",
            user_id=user_id or "",
            user_key=cookies or "",
            use_proxy=use_proxy
        )
        
        logger.info(f"🔄 检查扫码状态并尝试获取令牌...")
        
        # 执行一次轮询检�?检查扫码状�?获取token)
        token_result = await client.poll_device_token(
            device_code=device_code,
            code_verifier=code_verifier,
            qrcode_token=qrcode_token,
            max_attempts=1,  # 只尝试一�?            interval=0  # 不等�?        )
        
        if token_result.get('success'):
            new_user_key = token_result.get('user_key')  # 新的cookies
            new_user_id = token_result.get('user_id')  # 新的user_id
            
            # 纯Cookie模式：扫码登录只保存Cookie，不自动获取access_token
            # 如果用户需要开放平台API，需要后续手动点�?启用OPENAPI"
            
            # 更新cookies和user_id（扫码后获得的新凭证�?            if new_user_key:
                setattr(settings, 'pan115_user_key', new_user_key)
                # 同时保存到文�?                import os
                cookies_file = os.path.join('/app', 'config', '115-cookies.txt')
                os.makedirs(os.path.dirname(cookies_file), exist_ok=True)
                with open(cookies_file, 'w', encoding='utf-8') as f:
                    f.write(new_user_key)
                logger.info(f"�?新cookies已保存到文件")
            
            if new_user_id:
                setattr(settings, 'pan115_user_id', new_user_id)
            
            await db.commit()
            
            # 尝试刷新用户信息（使用Cookie�?            if new_user_key:
                client.user_key = new_user_key
                client.user_id = new_user_id
                
                user_info_result = await client.get_user_info()
                
                if user_info_result.get('success') and 'user_info' in user_info_result:
                    user_info = user_info_result['user_info']
                    # 缓存用户信息
                    import json
                    setattr(settings, 'pan115_user_info', json.dumps(user_info, ensure_ascii=False))
                    setattr(settings, 'pan115_last_refresh_at', get_user_now())
                    await db.commit()
                    
                    logger.info(f"�?用户信息已刷�?)
            
            return {
                "success": True,
                "status": "authorized",
                "message": "扫码登录成功"
            }
        else:
            error_msg = token_result.get('message', '')
            
            # 检查是否是等待状�?            if 'pending' in error_msg.lower() or 'waiting' in error_msg.lower():
                return {
                    "success": False,
                    "status": "pending",
                    "message": "等待用户授权..."
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "message": error_msg
                }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"�?轮询访问令牌异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qrcode")
async def get_qrcode_for_login(
    request: Pan115QRCodeRequest,
    current_user: User = Depends(get_current_user)
):
    """获取115登录二维�?""
    try:
        logger.info(f"📥 收到二维码请�? app_id={request.app_id}")
        
        # 创建临时客户端（只需要app_id�?        client = Pan115Client(
            app_id=request.app_id,
            app_key="",  # 不需要app_key
            user_id="",  # 登录前没有user_id
            user_key=""  # 登录前没有user_key
        )
        
        # 获取二维�?        result = await client.get_qrcode_token()
        
        if result['success']:
            logger.info(f"�?115二维码获取成�? token={result['qrcode_token']}")
            return {
                "success": True,
                "qrcode_token": result['qrcode_token'],
                "qrcode_url": result['qrcode_url'],
                "expires_in": result['expires_in']
            }
        else:
            logger.error(f"�?115二维码获取失�? {result.get('message')}")
            raise HTTPException(status_code=400, detail=result.get('message', '获取二维码失�?))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取115二维码异�? {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qrcode/status")
async def check_qrcode_login_status(
    data: Dict[str, str] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检�?15二维码扫码状�?""
    try:
        qrcode_token = data.get('qrcode_token')
        app_id = data.get('app_id')
        app = data.get('app', 'qandroid')  # 设备类型,默认为qandroid
        
        if not all([qrcode_token, app_id]):
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 创建临时客户�?        client = Pan115Client(
            app_id=app_id,
            app_key="",  # 不需要app_key
            user_id="",
            user_key=""
        )
        
        # 检查扫码状�?        result = await client.check_qrcode_status(qrcode_token)
        
        if not result['success']:
            return {
                "success": False,
                "status": result.get('status', 'error'),
                "message": result.get('message', '检查状态失�?)
            }
        
        status = result['status']
        
        # 如果已确认登录，保存用户凭据
        if status == 'confirmed':
            user_id = result.get('user_id')
            user_key = result.get('user_key')
            user_info = result.get('user_info', {})
            access_token = result.get('access_token')  # 🔑 获取access_token
            
            if user_id and user_key:
                # 保存到数据库
                settings_result = await db.execute(select(MediaSettings))
                settings = settings_result.scalars().first()
                
                if not settings:
                    settings = MediaSettings()
                    db.add(settings)
                
                settings.pan115_user_id = user_id
                settings.pan115_user_key = user_key
                settings.pan115_device_type = app  # 保存设备类型
                
                # 🔑 保存access_token(如果存在)
                # 注意: 扫码登录本身不返回access_token,只返回cookies
                if access_token:
                    # 有access_token: 设置2小时过期时间
                    settings.pan115_access_token = access_token
                    settings.pan115_token_expires_at = get_user_now() + timedelta(seconds=7200)
                    logger.info(f"🔑 已保存access_token到数据库,过期时间: {settings.pan115_token_expires_at}")
                else:
                    # 只有cookies: 不设置过期时�?�?15服务器控�?                    # cookies会一直有�?直到115服务器返�?01/403等错�?                    settings.pan115_access_token = None
                    settings.pan115_token_expires_at = None
                    logger.info(f"🍪 使用cookies登录,�?15服务器控制有效期(不主动失�?")
                
                # 保存完整的用户信息（JSON格式�?                import json
                settings.pan115_user_info = json.dumps(user_info, ensure_ascii=False)
                
                # 记录登录时间
                settings.pan115_last_refresh_at = get_user_now()
                
                await db.commit()
                
                logger.info(f"�?115用户登录成功并保�? user_id={user_id}, user_name={user_info.get('user_name', '')}, vip={user_info.get('vip_name', '普通用�?)}, device={app}, has_token={bool(access_token)}")
                
                return {
                    "success": True,
                    "status": "confirmed",
                    "user_id": user_id,
                    "user_info": user_info,  # 返回完整的用户信息给前端
                    "message": "登录成功"
                }
        
        return {
            "success": True,
            "status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检�?15扫码状态异�? {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-user-info")
async def refresh_pan115_user_info(
    force: bool = False,  # 是否强制刷新(忽略防抖)
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """刷新115网盘用户信息和空间信�?""
    try:
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            raise HTTPException(status_code=400, detail="未配�?15网盘")
        
        app_id = getattr(settings, 'pan115_app_id', None)
        app_key = getattr(settings, 'pan115_app_key', '')
        user_id = getattr(settings, 'pan115_user_id', None)
        user_key = getattr(settings, 'pan115_user_key', None)
        access_token = getattr(settings, 'pan115_access_token', None)
        token_expires_at = getattr(settings, 'pan115_token_expires_at', None)
        last_refresh_at = getattr(settings, 'pan115_last_refresh_at', None)
        
        if not user_id or not user_key:
            raise HTTPException(status_code=400, detail="请先登录115网盘")
        
        # 🔒 防抖检�? 如果距离上次刷新不到30秒且不是强制刷新,返回缓存
        if not force and last_refresh_at:
            time_since_last_refresh = (get_user_now() - last_refresh_at).total_seconds()
            if time_since_last_refresh < 30:
                logger.info(f"🔒 距离上次刷新仅{time_since_last_refresh:.1f}�?返回缓存数据(防抖)")
                try:
                    import json
                    cached_user_info_str = getattr(settings, 'pan115_user_info', None)
                    if cached_user_info_str:
                        cached_user_info = json.loads(cached_user_info_str)
                        return {
                            "success": True,
                            "message": f"刚刚已刷�?{time_since_last_refresh:.0f}秒前),返回缓存数据",
                            "user_info": cached_user_info,
                            "from_cache": True
                        }
                except Exception as e:
                    logger.warning(f"⚠️ 读取缓存失败: {e}")
        
        # 🔑 只检查access_token是否过期(不检查cookies过期,cookies�?15服务器控�?
        # 如果有access_token且已过期,则清空它;如果只有cookies,不主动失�?        if access_token and token_expires_at:
            if get_user_now() >= token_expires_at:
                logger.warning(f"⚠️ access_token已过�?清空并回退到cookies")
                access_token = None
                settings.pan115_access_token = None
                settings.pan115_token_expires_at = None
                await db.commit()
        elif not access_token and not token_expires_at:
            # 如果既没有access_token也没有过期时间记�?说明是纯cookies登录
            # 不设置过期时�?让cookies一直有效直�?15服务器拒绝为�?            logger.info(f"🍪 使用cookies登录,无过期时间限�?)
        
        # 使用 Pan115Client 获取最新的用户信息
        client = Pan115Client(
            app_id=app_id or "",
            app_key=app_key or "",
            user_id=user_id,
            user_key=user_key
        )
        
        # 🔑 如果access_token过期或不存在,且配置了AppID/AppKey,尝试获取新token
        if not access_token and app_id and app_key:
            logger.info(f"🔄 尝试获取新的access_token")
            token_result = await client.get_access_token()
            if token_result.get('success'):
                access_token = token_result.get('access_token')
                expires_in = token_result.get('expires_in', 7200)
                settings.pan115_access_token = access_token
                settings.pan115_token_expires_at = get_user_now() + timedelta(seconds=expires_in)
                await db.commit()
                logger.info(f"�?已获取新的access_token,有效期{expires_in}�?)
        
        # 🔑 如果有access_token,设置到client�?        if access_token:
            client.access_token = access_token
            logger.info(f"🔑 使用access_token刷新用户信息(过期时间: {token_expires_at})")
        else:
            logger.info(f"📡 使用Web API刷新用户信息(无access_token)")
        
        logger.info(f"🔄 开始刷新用户信�? user_id={user_id}")
        
        # 获取最新的用户信息和空间信�?        user_info_result = await client.get_user_info()
        
        if user_info_result.get('success') and 'user_info' in user_info_result:
            user_info = user_info_result['user_info']
            
            # 🔍 检查是否真的获取到了有效数�?空间信息不为0)
            space_total = user_info.get('space', {}).get('total', 0)
            has_valid_space = space_total > 0
            
            # 如果获取到有效数�?更新缓存;否则保留原缓�?            if has_valid_space:
                try:
                    import json
                    setattr(settings, 'pan115_user_info', json.dumps(user_info, ensure_ascii=False))
                    # 🕐 更新最后刷新时�?                    settings.pan115_last_refresh_at = get_user_now()
                    await db.commit()
                    logger.info(f"�?用户信息已刷新并缓存: {user_info.get('user_name', 'N/A')}, 空间: {space_total / 1024 / 1024 / 1024:.2f}GB")
                except Exception as cache_error:
                    logger.warning(f"⚠️ 更新用户信息缓存失败: {cache_error}")
                
                return {
                    "success": True,
                    "message": "�?用户信息已刷�?,
                    "user_info": user_info,
                    "refreshed_at": settings.pan115_last_refresh_at.isoformat() if settings.pan115_last_refresh_at else None
                }
            else:
                # 空间信息�?,说明API调用失败,返回缓存数据
                logger.warning(f"⚠️ 刷新失败(空间信息�?),保留原缓存数�?)
                
                # 尝试从缓存读�?                try:
                    import json
                    cached_user_info_str = getattr(settings, 'pan115_user_info', None)
                    if cached_user_info_str:
                        cached_user_info = json.loads(cached_user_info_str)
                        logger.info(f"💾 返回缓存的用户信�?)
                        return {
                            "success": True,
                            "message": "API调用失败,返回缓存数据",
                            "user_info": cached_user_info,
                            "from_cache": True
                        }
                except Exception as e:
                    logger.error(f"�?读取缓存失败: {e}")
                
                # 如果缓存也没�?抛出错误
                raise HTTPException(status_code=400, detail="刷新失败且无缓存数据")
        else:
            error_msg = user_info_result.get('message', '刷新失败')
            logger.warning(f"⚠️ 刷新用户信息失败: {error_msg}")
            
            # 尝试返回缓存数据而不是直接报�?            try:
                import json
                cached_user_info_str = getattr(settings, 'pan115_user_info', None)
                if cached_user_info_str:
                    cached_user_info = json.loads(cached_user_info_str)
                    logger.info(f"💾 刷新失败,返回缓存的用户信�?)
                    return {
                        "success": True,
                        "message": f"刷新失败({error_msg}),返回缓存数据",
                        "user_info": cached_user_info,
                        "from_cache": True
                    }
            except Exception as e:
                logger.error(f"�?读取缓存失败: {e}")
            
            raise HTTPException(status_code=400, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新115用户信息异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_pan115_connection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试115网盘连接并刷新用户信息（使用 Pan115Client�?""
    try:
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            raise HTTPException(status_code=400, detail="未配�?15网盘")
        
        app_id = getattr(settings, 'pan115_app_id', None)
        user_id = getattr(settings, 'pan115_user_id', None)
        user_key = getattr(settings, 'pan115_user_key', None)
        
        if not user_id or not user_key:
            raise HTTPException(status_code=400, detail="请先登录115网盘")
        
        # 使用 Pan115Client 测试连接并获取最新的用户信息
        client = Pan115Client(
            app_id=app_id or "",
            app_key="",
            user_id=user_id,
            user_key=user_key
        )
        
        # 获取最新的用户信息和空间信�?        user_info_result = await client.get_user_info()
        
        if user_info_result.get('success') and 'user_info' in user_info_result:
            user_info = user_info_result['user_info']
            
            # 更新数据库缓�?            try:
                import json
                setattr(settings, 'pan115_user_info', json.dumps(user_info, ensure_ascii=False))
                await db.commit()
                logger.info(f"�?测试连接成功，已更新用户信息缓存")
            except Exception as cache_error:
                logger.warning(f"⚠️ 更新用户信息缓存失败: {cache_error}")
            
            return {
                "success": True,
                "message": "连接成功，用户信息已刷新",
                "user_id": user_id,
                "user_info": user_info
            }
        else:
            error_msg = user_info_result.get('message', '连接失败')
            logger.warning(f"⚠️ 测试连接失败: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试115连接异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_to_pan115(
    file_path: str = Body(...),
    remote_path: str = Body(default="/telegram_downloads"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文件�?15网盘（使�?Pan115Client�?""
    try:
        from pathlib import Path
        
        # 检查文件是否存�?        if not Path(file_path).exists():
            raise HTTPException(status_code=400, detail=f"文件不存�? {file_path}")
        
        # 获取115登录信息
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            raise HTTPException(status_code=400, detail="未配�?15网盘")
        
        app_id = getattr(settings, 'pan115_app_id', None)
        user_id = getattr(settings, 'pan115_user_id', None)
        user_key = getattr(settings, 'pan115_user_key', None)
        
        if not all([app_id, user_id, user_key]):
            raise HTTPException(status_code=400, detail="请先配置并登�?15网盘")
        
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
            logger.info(f"�?文件上传成功: {Path(file_path).name}")
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
        logger.error(f"�?上传文件异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 常规扫码登录（非 Open API�?===================

class RegularQRCodeRequest(BaseModel):
    """常规115登录二维码请�?""
    app: str = "web"  # 应用类型：web/android/ios/tv/alipaymini/wechatmini/qandroid


@router.post("/regular-qrcode")
async def get_regular_qrcode(
    request: RegularQRCodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取常规115登录二维码（使用 Pan115Client�?""
    try:
        logger.info(f"📱 获取常规115登录二维�? app={request.app} (类型: {type(request.app)})")
        logger.info(f"📱 完整请求对象: {request}")
        
        # 从数据库读取配置（如果有AppID，会使用开放平台二维码�?        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        app_id = getattr(settings, 'pan115_app_id', '') if settings else ''
        use_proxy = getattr(settings, 'pan115_use_proxy', False) if settings else False
        
        # 创建临时客户端获取二维码
        temp_client = Pan115Client(
            app_id=app_id,  # 如果有AppID，会使用开放平台二维码
            app_key="",
            user_id="",
            user_key="",
            use_proxy=use_proxy
        )
        result = await temp_client.get_regular_qrcode(app=request.app)
        
        if result.get('success'):
            logger.info(f"�?二维码获取成�? token={result['qrcode_token'].get('uid')}, app={request.app}")
            # 在返回结果中包含设备类型,方便前端使用
            result['device_type'] = request.app
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('message', '获取二维码失�?))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"�?获取常规115登录二维码失�? {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regular-qrcode/status")
async def check_regular_qrcode_status(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查常�?15登录二维码状态（使用 Pan115Client�?""
    try:
        # 添加详细的请求日�?        logger.info(f"📥 收到二维码状态检查请�? {request}")
        
        qrcode_token = request.get('qrcode_token')
        app = request.get('app', 'web')
        
        logger.info(f"📦 解析参数: qrcode_token={qrcode_token}, app={app}")
        
        if not qrcode_token:
            logger.error("�?缺少qrcode_token参数")
            raise HTTPException(status_code=400, detail="缺少qrcode_token参数")
        
        logger.info(f"🔍 检查常�?15登录二维码状�? uid={qrcode_token.get('uid') if isinstance(qrcode_token, dict) else 'N/A'}, app={app}")
        
        # 从数据库读取代理配置
        result_db = await db.execute(select(MediaSettings))
        settings = result_db.scalars().first()
        use_proxy = getattr(settings, 'pan115_use_proxy', False) if settings else False
        
        # 创建临时客户端检查状�?        temp_client = Pan115Client(
            app_id="",
            app_key="",
            user_id="",
            user_key="",
            use_proxy=use_proxy
        )
        result = await temp_client.check_regular_qrcode_status(qrcode_token, app)
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', '检查状态失�?))
        
        # 如果登录成功，保存cookies到数据库
        if result.get('status') == 'confirmed':
            cookies = result.get('cookies')
            user_id = result.get('user_id')
            user_info = result.get('user_info', {})
            access_token = result.get('access_token')  # 🔑 获取access_token
            
            if cookies and user_id:
                # 保存到数据库
                db_result = await db.execute(select(MediaSettings))
                settings = db_result.scalars().first()
                if not settings:
                    settings = MediaSettings()
                    db.add(settings)
                
                # 常规登录存储 cookies
                # 注意：这里存储的�?cookies，不�?Open API �?user_key
                setattr(settings, 'pan115_user_id', user_id)
                setattr(settings, 'pan115_user_key', cookies)
                
                # 💾 同时保存cookies到文�?持久�?
                try:
                    import os
                    cookies_dir = os.path.join('/app', 'config')
                    os.makedirs(cookies_dir, exist_ok=True)
                    cookies_file = os.path.join(cookies_dir, '115-cookies.txt')
                    
                    with open(cookies_file, 'w', encoding='utf-8') as f:
                        f.write(cookies)
                    
                    logger.info(f"�?Cookies已保存到文件: {cookies_file}")
                except Exception as save_error:
                    logger.warning(f"⚠️ 保存cookies到文件失�? {save_error}")  # 复用字段存储 cookies
                setattr(settings, 'pan115_device_type', app)
                
                # 🔑 保存access_token(如果存在)
                # 注意: 扫码登录本身不返回access_token,只返回cookies
                # cookies的有效期通常�?0�?比access_token(2小时)长得�?                if access_token:
                    setattr(settings, 'pan115_access_token', access_token)
                    setattr(settings, 'pan115_token_expires_at', get_user_now() + timedelta(seconds=7200))
                    logger.info(f"🔑 已保存access_token到数据库(有效�?小时)")
                else:
                    # 没有access_token�?设置cookies的预估过期时间为30�?                    setattr(settings, 'pan115_token_expires_at', get_user_now() + timedelta(days=30))
                    logger.info(f"🍪 使用cookies登录,预估有效�?0�?)
                
                # 保存完整的用户信息到数据库（JSON格式�?                try:
                    import json
                    setattr(settings, 'pan115_user_info', json.dumps(user_info, ensure_ascii=False))
                    # 🕐 记录登录时间
                    setattr(settings, 'pan115_last_refresh_at', get_user_now())
                    logger.info(f"💾 已保存用户信息到数据�? {user_info.get('user_name', 'N/A')}, VIP={user_info.get('vip_name', '普通用�?)}")
                except Exception as json_error:
                    logger.warning(f"⚠️ 保存用户信息失败: {json_error}")
                
                await db.commit()
                
                logger.info(f"�?115常规登录成功并已保存: UID={user_id}, 用户�?{user_info.get('user_name', 'N/A')}, has_token={bool(access_token)}")
                
                # 在返回结果中添加用户信息用于前端显示
                result['user_info'] = user_info
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"�?检查常�?15登录二维码状态失�? {e}")
        raise HTTPException(status_code=500, detail=str(e))

