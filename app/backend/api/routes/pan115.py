"""
115网盘配置和登录API（完全基于Web API，不依赖开放平台）
"""
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from pydantic import BaseModel

from database import get_db
from models import User, MediaSettings
from api.dependencies import get_current_user
from services.pan115_client import Pan115Client
from log_manager import get_logger
from timezone_utils import get_user_now

logger = get_logger('pan115_api')

router = APIRouter(tags=["115网盘"])


# ==================== 辅助函数 ====================

async def get_pan115_settings_for_webapi(db: AsyncSession) -> MediaSettings:
    """
    获取115网盘配置的原始settings对象（用于Web API）
    
    用于离线下载、分享链接等功能，只需要Cookie（user_id + user_key），
    不需要开放平台的AppID/AppSecret
    """
    result = await db.execute(select(MediaSettings))
    settings = result.scalars().first()
    
    if not settings:
        raise HTTPException(status_code=404, detail="115网盘未配置")
    
    # 检查是否已配置Cookie（只要有user_id和user_key就可以使用Web API）
    user_id = getattr(settings, 'pan115_user_id', None)
    user_key = getattr(settings, 'pan115_user_key', None)
    
    if not user_id or not user_key:
        raise HTTPException(
            status_code=400, 
            detail="115网盘Cookie未配置，请先扫码登录获取Cookie"
        )
    
    return settings


def create_pan115_client_for_webapi(settings: MediaSettings) -> Pan115Client:
    """
    创建Pan115Client实例（仅用于Web API）
    
    不传入app_id和app_secret，只使用Cookie（user_id + user_key）
    用于所有115功能（离线下载、分享链接、文件管理等）
    
    Args:
        settings: 媒体设置对象
    """
    use_proxy = getattr(settings, 'pan115_use_proxy', False) or False
    user_id = getattr(settings, 'pan115_user_id', '') or ''
    user_key = getattr(settings, 'pan115_user_key', '') or ''
    
    # 不传入app_id和app_secret，强制使用Web API
    return Pan115Client(
        app_id="",  # 留空，使用Web API
        app_key="",
        user_id=user_id,
        user_key=user_key,
        use_proxy=use_proxy
    )


# ==================== 数据模型 ====================

class Pan115ConfigUpdate(BaseModel):
    """115网盘配置更新（仅Web API）"""
    pan115_user_id: Optional[str] = None  # 手动输入的user_id（Cookie）
    pan115_user_key: Optional[str] = None  # 手动输入的user_key（Cookie）
    pan115_request_interval: Optional[float] = 1.0  # API请求间隔（秒）
    pan115_device_type: Optional[str] = None  # 登录设备类型
    pan115_use_proxy: Optional[bool] = None  # 是否使用代理


class ShareInfoRequest(BaseModel):
    """获取分享信息请求"""
    share_code: str
    receive_code: Optional[str] = None


class SaveShareRequest(BaseModel):
    """转存分享链接请求"""
    share_code: str
    receive_code: Optional[str] = None
    target_dir_id: str = "0"
    file_ids: Optional[List[str]] = None


# ==================== 扫码登录（常规二维码）请求体 ====================

class RegularQRCodeRequest(BaseModel):
    """获取常规二维码的请求体"""
    app: str = "qandroid"


class RegularQRCodeStatusRequest(BaseModel):
    """检查常规二维码状态请求体"""
    qrcode_token: dict
    app: str = "qandroid"


# ==================== 配置管理 ====================

@router.get("/config")
async def get_pan115_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取115网盘配置（仅Web API）"""
    try:
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            return {
                "pan115_user_id": None,
                "pan115_user_key": None,
                "pan115_request_interval": 1.0,
                "pan115_use_proxy": False,
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
            "pan115_user_id": getattr(settings, 'pan115_user_id', None),
            "pan115_user_key": user_key_masked,
            "pan115_request_interval": getattr(settings, 'pan115_request_interval', 1.0),
            "pan115_device_type": getattr(settings, 'pan115_device_type', 'qandroid'),
            "pan115_use_proxy": getattr(settings, 'pan115_use_proxy', False),
            "is_configured": is_configured
        }
        
        # 如果已登录，尝试获取用户详细信息
        if is_configured:
            try:
                # 优先使用数据库中保存的用户信息（登录时保存的）
                if hasattr(settings, 'pan115_user_info') and settings.pan115_user_info:
                    try:
                        import json
                        cached_user_info = json.loads(settings.pan115_user_info)
                        result['user_info'] = cached_user_info
                        logger.info(f"✅ 使用缓存的用户信息: {cached_user_info.get('user_name', 'N/A')}")
                    except Exception as parse_error:
                        logger.warning(f"⚠️ 解析缓存的用户信息失败: {parse_error}")
                
                # 如果没有缓存的用户信息，从Web API获取
                if 'user_info' not in result:
                    client = create_pan115_client_for_webapi(settings)
                    user_info_result = await client.get_user_info()
                    
                    if user_info_result.get('success') and 'user_info' in user_info_result:
                        result['user_info'] = user_info_result['user_info']
                        
                        # 更新数据库缓存
                        try:
                            import json
                            settings.pan115_user_info = json.dumps(user_info_result['user_info'], ensure_ascii=False)
                            await db.commit()
                        except Exception as update_error:
                            logger.warning(f"⚠️ 更新用户信息缓存失败: {update_error}")
                        
            except Exception as e:
                logger.error(f"❌ 获取用户信息异常: {e}")
        
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
    """更新115网盘配置（仅Web API）"""
    try:
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            # 创建默认配置
            settings = MediaSettings()
            db.add(settings)
        
        # 更新配置（使用setattr以支持动态字段）
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
        
        logger.info(f"✅ 115网盘配置已更新: user_id={config.pan115_user_id if config.pan115_user_id else '未设置'}")
        
        return {
            "success": True,
            "message": "115网盘配置已更新"
        }
        
    except Exception as e:
        logger.error(f"更新115网盘配置失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 扫码登录（Web API）====================

@router.post("/qrcode")
async def generate_qrcode(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成115扫码登录二维码（Web API方式）
    
    不需要AppID，纯Cookie登录
    """
    try:
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        use_proxy = getattr(settings, 'pan115_use_proxy', False) if settings else False
        
        logger.info(f"📱 生成115扫码登录二维码（Web API）")
        
        # 创建临时客户端（不需要AppID）
        temp_client = Pan115Client(
            app_id="",  # 不需要AppID
            app_key="",
            user_id="",
            user_key="",
            use_proxy=use_proxy
        )
        
        # 生成二维码
        qrcode_result = await temp_client.generate_qrcode()
        
        if qrcode_result.get('success'):
            return {
                "success": True,
                "qrcode_url": qrcode_result.get('qrcode_url'),
                "qrcode_token": qrcode_result.get('qrcode_token'),
                "message": "二维码生成成功"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=qrcode_result.get('message', '二维码生成失败')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 生成二维码异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regular-qrcode")
async def generate_regular_qrcode(
    payload: RegularQRCodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取常规115二维码（不使用开放平台），用于APP扫码登录。
    对应前端 /api/pan115/regular-qrcode。
    """
    try:
        logger.info(f"📱 生成常规115二维码: app={payload.app}")
        # 常规二维码不需要读取数据库配置
        temp_client = Pan115Client(app_id="", app_key="", user_id="", user_key="")
        result = await temp_client.get_regular_qrcode(app=payload.app)
        if result.get('success'):
            return {
                "success": True,
                "qrcode_url": result.get('qrcode_url'),
                "qrcode_token": result.get('qrcode_token'),
                # 返回归一化后的 app，供前端用同样的类型继续轮询
                "app": result.get('app') or payload.app,
                "device_type": result.get('app') or payload.app
            }
        raise HTTPException(status_code=400, detail=result.get('message', '获取二维码失败'))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 生成常规二维码异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qrcode/status")
async def check_qrcode_status(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    检查二维码扫描状态并完成登录（Web API方式）
    
    不需要AppID，只获取Cookie
    """
    try:
        qrcode_token = data.get('qrcode_token')
        
        if not qrcode_token:
            raise HTTPException(status_code=400, detail="缺少qrcode_token参数")
        
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        if not settings:
            settings = MediaSettings()
            db.add(settings)
        
        use_proxy = getattr(settings, 'pan115_use_proxy', False)
        
        # 创建临时客户端
        temp_client = Pan115Client(
            app_id="",
            app_key="",
            user_id="",
            user_key="",
            use_proxy=use_proxy
        )
        
        # 检查扫码状态
        status_result = await temp_client.check_qrcode_status(qrcode_token)
        
        if status_result.get('success') and status_result.get('status') == 'authorized':
            # 扫码成功，保存Cookie
            user_id = status_result.get('user_id')
            user_key = status_result.get('user_key')  # Cookie
            user_info = status_result.get('user_info', {})
            
            if user_id and user_key:
                # 保存到数据库
                setattr(settings, 'pan115_user_id', user_id)
                setattr(settings, 'pan115_user_key', user_key)
                
                # 保存用户信息
                if user_info:
                    import json
                    setattr(settings, 'pan115_user_info', json.dumps(user_info, ensure_ascii=False))
                
                await db.commit()
                
                # 同时保存Cookie到文件（可选）
                import os
                cookies_file = os.path.join('/app', 'config', '115-cookies.txt')
                os.makedirs(os.path.dirname(cookies_file), exist_ok=True)
                with open(cookies_file, 'w', encoding='utf-8') as f:
                    f.write(user_key)
                
                logger.info(f"✅ 115用户登录成功: user_id={user_id}, user_name={user_info.get('user_name', 'N/A')}")
                
                return {
                    "success": True,
                    "status": "authorized",
                    "message": "扫码登录成功",
                    "user_info": user_info
                }
        
        # 返回当前状态
        return {
            "success": status_result.get('success', False),
            "status": status_result.get('status', 'pending'),
            "message": status_result.get('message', '等待扫码...')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 检查二维码状态异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regular-qrcode/status")
async def check_regular_qrcode_status(
    payload: RegularQRCodeStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    检查常规二维码扫码状态，并在确认后保存 cookies 到数据库。
    对应前端 /api/pan115/regular-qrcode/status。
    """
    try:
        app = payload.app or "qandroid"
        token = payload.qrcode_token or {}
        temp_client = Pan115Client(app_id="", app_key="", user_id="", user_key="")
        status_result = await temp_client.check_regular_qrcode_status(token, app=app)

        if status_result.get('success') and status_result.get('status') == 'confirmed':
            # 保存到数据库
            result = await db.execute(select(MediaSettings))
            settings = result.scalars().first()
            if not settings:
                settings = MediaSettings()
                db.add(settings)

            user_id = status_result.get('user_id')
            cookies_str = status_result.get('cookies') or status_result.get('user_key')
            user_info = status_result.get('user_info', {})

            if user_id and cookies_str:
                setattr(settings, 'pan115_user_id', user_id)
                setattr(settings, 'pan115_user_key', cookies_str)
                # 缓存用户信息
                if user_info:
                    import json
                    setattr(settings, 'pan115_user_info', json.dumps(user_info, ensure_ascii=False))
                await db.commit()

            return {
                "success": True,
                "status": "confirmed",
                "message": "扫码登录成功",
                "user_info": user_info
            }

        return {
            "success": status_result.get('success', False),
            "status": status_result.get('status', 'pending'),
            "message": status_result.get('message', '等待扫码...')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 检查常规二维码状态异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 测试连接 ====================

@router.post("/test")
async def test_pan115_connection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试115网盘连接并刷新用户信息（使用 Web API）"""
    try:
        # 获取115网盘配置（仅需Cookie）
        settings = await get_pan115_settings_for_webapi(db)
        
        # 创建Web API客户端（不需要AppID）
        client = create_pan115_client_for_webapi(settings)
        
        # 获取最新的用户信息和空间信息
        user_info_result = await client.get_user_info()
        
        if user_info_result.get('success') and 'user_info' in user_info_result:
            user_info = user_info_result['user_info']
            
            # 更新数据库缓存
            try:
                import json
                setattr(settings, 'pan115_user_info', json.dumps(user_info, ensure_ascii=False))
                await db.commit()
                logger.info(f"✅ 测试连接成功，已更新用户信息缓存")
            except Exception as cache_error:
                logger.warning(f"⚠️ 更新用户信息缓存失败: {cache_error}")
            
            user_id = getattr(settings, 'pan115_user_id', None)
            
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


@router.post("/test-cookies")
async def test_cookies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试已保存 cookies 是否有效（前端“检测可用性”按钮）。"""
    try:
        settings = await get_pan115_settings_for_webapi(db)
        client = create_pan115_client_for_webapi(settings)
        result = await client.get_user_info()
        if result.get('success'):
            return {"success": True, "message": "Cookies 可用", "user_info": result.get('user_info')}
        raise HTTPException(status_code=400, detail=result.get('message', 'Cookies 无效'))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 测试cookies异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-user-info")
async def refresh_user_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """刷新用户信息（与前端路径保持一致）。"""
    try:
        settings = await get_pan115_settings_for_webapi(db)
        client = create_pan115_client_for_webapi(settings)
        user_info_result = await client.get_user_info()
        if user_info_result.get('success'):
            # 更新缓存
            try:
                import json
                settings.pan115_user_info = json.dumps(user_info_result['user_info'], ensure_ascii=False)
                await db.commit()
            except Exception as cache_error:
                logger.warning(f"⚠️ 更新用户信息缓存失败: {cache_error}")
            return {"success": True, "message": "用户信息已刷新", "user_info": user_info_result['user_info']}
        raise HTTPException(status_code=400, detail=user_info_result.get('message', '刷新失败'))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 刷新用户信息异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/activate-open-api")
async def activate_open_api(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    激活开放平台API（最小实现）：
    目前基于已登录 cookies 调用用户信息接口确认可用性，并返回空间信息是否可用。
    """
    try:
        settings = await get_pan115_settings_for_webapi(db)
        client = create_pan115_client_for_webapi(settings)
        user_info_result = await client.get_user_info()
        if user_info_result.get('success'):
            has_space_info = bool(user_info_result.get('user_info', {}).get('space', {}).get('total', 0))
            return {
                "success": True,
                "message": "开放平台API已激活或可用",
                "has_space_info": has_space_info,
                "user_info": user_info_result.get('user_info')
            }
        raise HTTPException(status_code=400, detail=user_info_result.get('message', '激活失败'))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 激活开放平台API异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 离线下载管理 ====================

@router.post("/offline/add")
async def add_offline_task(
    url: str = Body(..., description="下载链接（HTTP/磁力/BT）"),
    target_dir_id: str = Body("0", description="目标目录ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    添加离线下载任务（使用Web API，只需Cookie）
    
    支持的链接类型：
    - HTTP/HTTPS 直链
    - 磁力链接 (magnet:)
    - BT种子 URL
    """
    try:
        # 获取115网盘配置（仅需Cookie）
        settings = await get_pan115_settings_for_webapi(db)
        
        # 创建Web API客户端（不需要AppID）
        client = create_pan115_client_for_webapi(settings)
        
        # 添加离线任务
        result = await client.add_offline_task(url, target_dir_id)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 添加离线任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/offline/tasks")
async def get_offline_tasks(
    page: int = Query(1, ge=1, description="页码"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取离线任务列表（使用Web API，只需Cookie）
    
    返回任务信息：
    - task_id: 任务ID
    - name: 任务名称
    - status: 状态码 (-1=等待, 0=下载中, 1=已完成, 2=失败, 4=已删除)
    - status_text: 状态文本
    - size: 文件大小
    - percentDone: 完成百分比
    - add_time: 添加时间
    - file_id: 完成后的文件ID
    """
    try:
        # 获取115网盘配置（仅需Cookie）
        settings = await get_pan115_settings_for_webapi(db)
        
        # 创建Web API客户端（不需要AppID）
        client = create_pan115_client_for_webapi(settings)
        
        # 获取离线任务列表
        result = await client.get_offline_tasks(page)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取离线任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/offline/tasks")
async def delete_offline_tasks(
    task_ids: List[str] = Body(..., description="要删除的任务ID列表"),
    db: AsyncSession = Depends(get_db)
):
    """
    删除离线任务（使用Web API，只需Cookie）
    
    支持批量删除多个任务
    """
    try:
        # 获取115网盘配置（仅需Cookie）
        settings = await get_pan115_settings_for_webapi(db)
        
        # 创建Web API客户端（不需要AppID）
        client = create_pan115_client_for_webapi(settings)
        
        # 删除离线任务
        result = await client.delete_offline_task(task_ids)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除离线任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/offline/clear")
async def clear_offline_tasks(
    flag: int = Body(1, ge=0, le=2, description="清空标志：0=所有，1=已完成，2=失败"),
    db: AsyncSession = Depends(get_db)
):
    """
    清空离线任务（使用Web API，只需Cookie）
    
    flag 参数：
    - 0: 清空所有任务（慎用）
    - 1: 清空已完成任务（推荐）
    - 2: 清空失败任务
    """
    try:
        # 获取115网盘配置（仅需Cookie）
        settings = await get_pan115_settings_for_webapi(db)
        
        # 创建Web API客户端（不需要AppID）
        client = create_pan115_client_for_webapi(settings)
        
        # 清空离线任务
        result = await client.clear_offline_tasks(flag)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 清空离线任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 分享链接管理 ====================

@router.post("/share/info")
async def get_share_info(
    payload: ShareInfoRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    获取115分享链接信息（使用Web API，只需Cookie）
    
    支持：
    - 无密码分享
    - 有密码分享（需要提供 receive_code）
    """
    try:
        # 获取115网盘配置（仅需Cookie）
        settings = await get_pan115_settings_for_webapi(db)
        
        # 创建Web API客户端（不需要AppID）
        client = create_pan115_client_for_webapi(settings)
        
        # 获取分享信息
        result = await client.get_share_info(
            share_code=payload.share_code,
            receive_code=payload.receive_code
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取分享信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/share/save")
async def save_share(
    payload: SaveShareRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    转存115分享链接到我的网盘（使用Web API，只需Cookie）
    
    参数：
    - share_code: 分享码（从链接提取，如 sw1abc123）
    - receive_code: 提取码（如果分享有密码）
    - target_dir_id: 目标目录ID（默认根目录）
    - file_ids: 要转存的文件ID列表（可选，为空则转存全部）
    """
    try:
        # 获取115网盘配置（仅需Cookie）
        settings = await get_pan115_settings_for_webapi(db)
        
        # 创建Web API客户端（不需要AppID）
        client = create_pan115_client_for_webapi(settings)
        
        logger.info(f"📥 转存分享链接: share_code={payload.share_code}, target_dir={payload.target_dir_id}")
        
        # 转存分享
        result = await client.save_share(
            share_code=payload.share_code,
            receive_code=payload.receive_code,
            target_dir_id=payload.target_dir_id,
            file_ids=payload.file_ids
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        logger.info(f"✅ 转存成功: {result.get('saved_count', 0)} 个文件")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 转存分享链接失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
