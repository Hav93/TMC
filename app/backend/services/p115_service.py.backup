"""
115网盘服务 - 使用p115client SDK (Python 3.12+)
混合方案：支持常规登录和开放平台API
"""
import os
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from p115client import P115Client
from log_manager import get_logger

logger = get_logger('p115_service')

# 支持的设备类型（直接使用p115client的app参数）
SUPPORTED_DEVICE_TYPES = [
    'qandroid',    # 115生活 - Android端
    'qios',        # 115生活 - iOS端  
    'android',     # 115网盘 - Android端
    'ios',         # 115网盘 - iOS端
    'ipad',        # 115网盘 - iPad端
    'web',         # 网页版
    'harmony',     # 鸿蒙系统
    'alipaymini',  # 支付宝小程序
    'wechatmini',  # 微信小程序
]

# VIP等级名称映射
VIP_LEVEL_NAMES = {
    0: '普通用户',
    1: '原石会员',
    2: '尝鲜VIP',
    3: '体验VIP',
    4: '月费VIP',
    5: '年费VIP',
    6: '年费VIP高级版',
    7: '年费VIP特级版',
    8: '超级VIP',
    9: '长期VIP',
}


class P115Service:
    """115网盘服务封装类"""
    
    def __init__(self, cookies: Optional[str] = None):
        """
        初始化115服务
        
        Args:
            cookies: 115登录cookies (格式: "UID=xxx; CID=xxx; SEID=xxx")
        """
        self.client: Optional[P115Client] = None
        self.cookies = cookies
        
        if cookies:
            try:
                self.client = P115Client(cookies=cookies)
                logger.info("✅ P115Client初始化成功（使用cookies）")
            except Exception as e:
                logger.error(f"❌ P115Client初始化失败: {e}")
    
    async def qrcode_login(self, device_type: str = 'qandroid') -> Dict[str, Any]:
        """
        获取二维码登录信息
        
        Args:
            device_type: 设备类型 (qandroid/qios/android/ios/ipad/web/harmony/alipaymini/wechatmini)
        
        Returns:
            {
                "success": bool,
                "qrcode_url": str,  # 二维码图片URL
                "qrcode_token": str,  # 用于轮询状态的token
                "expires_in": int  # 过期时间（秒）
            }
        """
        try:
            # 验证设备类型
            if device_type not in SUPPORTED_DEVICE_TYPES:
                device_type = 'qandroid'  # 默认使用115生活Android
            
            logger.info(f"📱 获取二维码: 设备类型={device_type}")
            
            # p115client的QR code登录是同步的，需要在线程池中执行
            loop = asyncio.get_event_loop()
            
            def _get_qrcode():
                # 使用静态方法获取二维码token，传入设备类型
                qrcode_result = P115Client.login_qrcode_token(app=device_type)
                
                # 检查返回状态
                if qrcode_result.get('state') != 1:
                    raise Exception(f"获取二维码失败: {qrcode_result}")
                
                data = qrcode_result.get('data', {})
                return {
                    "success": True,
                    "qrcode_url": data.get('qrcode'),
                    "qrcode_token": data.get('uid'),
                    "qrcode_token_data": {  # 完整的token数据，用于状态检查
                        "uid": data.get('uid'),
                        "time": data.get('time'),
                        "sign": data.get('sign')
                    },
                    "device_type": device_type,
                    "expires_in": 300  # 默认5分钟
                }
            
            result = await loop.run_in_executor(None, _get_qrcode)
            logger.info(f"✅ 获取二维码成功: token={result['qrcode_token']}, device={device_type}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 获取二维码失败: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    async def check_qrcode_status(self, qrcode_token_data: Dict[str, Any], device_type: str = 'qandroid') -> Dict[str, Any]:
        """
        检查二维码扫码状态 - 使用p115client的scan_result方法
        
        Args:
            qrcode_token_data: 二维码token完整数据 {'uid': str, 'time': int, 'sign': str}
            device_type: 设备类型
            
        Returns:
            {
                "success": bool,
                "status": str,  # waiting/scanned/confirmed/expired
                "cookies": str,  # 登录成功后的cookies
                "user_id": str  # 用户ID
            }
        """
        try:
            loop = asyncio.get_event_loop()
            
            def _check_status():
                """使用p115client检查扫码状态"""
                try:
                    logger.info(f"🔍 检查扫码状态: token={qrcode_token_data}, device={device_type}")
                    
                    # 步骤1: 使用login_qrcode_scan_status检查状态
                    status_result = P115Client.login_qrcode_scan_status(qrcode_token_data)
                    logger.info(f"📱 状态检查返回: {status_result}")
                    
                    # 解析状态
                    # state=1表示成功, data.status表示扫码状态
                    if status_result.get('state') != 1:
                        return {"success": True, "status": "waiting"}
                    
                    scan_data = status_result.get('data', {})
                    scan_status = scan_data.get('status', 0)
                    
                    if scan_status == 2:
                        # 已确认登录，获取cookies
                        uid = qrcode_token_data.get('uid')
                        logger.info(f"✅ 扫码已确认，获取登录凭证: uid={uid}")
                        
                        # 步骤2: 使用login_qrcode_scan_result获取cookies
                        login_result = P115Client.login_qrcode_scan_result(
                            uid,  # 传递uid字符串
                            app=device_type
                        )
                        logger.info(f"🔐 登录结果: {login_result}")
                        
                        # 提取cookies
                        if login_result.get('state') == 1 and login_result.get('data'):
                            data = login_result['data']
                            uid_val = data.get('user_id') or data.get('uid')
                            
                            # cookies在data.cookie字段里
                            cookie_dict = data.get('cookie', {})
                            if not cookie_dict:
                                # 兼容：也检查直接在data下的情况
                                cookie_dict = {k: data[k] for k in ['UID', 'CID', 'SEID'] if k in data}
                            
                            # 构建cookies字符串（包含所有必要的cookie字段）
                            cookies_parts = []
                            for key in ['UID', 'CID', 'SEID', 'KID']:
                                if key in cookie_dict:
                                    cookies_parts.append(f"{key}={cookie_dict[key]}")
                            
                            if cookies_parts and uid_val:
                                cookies_str = '; '.join(cookies_parts)
                                logger.info(f"✅ 115登录成功: UID={uid_val}, Cookies={cookies_str[:50]}...")
                                
                                # 提取用户信息
                                user_info = {
                                    'user_id': uid_val,
                                    'user_name': data.get('user_name', ''),
                                    'email': data.get('email', ''),
                                    'mobile': data.get('mobile', ''),
                                    'is_vip': data.get('is_vip', 0),
                                    'face': data.get('face', {}),
                                    'country': data.get('country', ''),
                                }
                                
                                return {
                                    "success": True,
                                    "status": "confirmed",
                                    "cookies": cookies_str,
                                    "user_id": str(uid_val),
                                    "user_info": user_info
                                }
                        
                        # 如果获取cookies失败，返回错误
                        logger.error(f"❌ 获取cookies失败: {login_result}")
                        return {"success": False, "status": "error", "message": "获取登录凭证失败"}
                        
                    elif scan_status == 1:
                        # 已扫码，等待确认
                        return {"success": True, "status": "scanned"}
                    elif scan_status in [-1, -2]:
                        # 已过期或取消
                        return {"success": True, "status": "expired"}
                    else:
                        # 等待扫码 (status=0)
                        return {"success": True, "status": "waiting"}
                        
                except Exception as e:
                    error_msg = str(e)
                    logger.info(f"⚠️ 状态检查异常: {error_msg}")
                    
                    # 判断错误类型
                    if "aborted" in error_msg or "timeout" in error_msg:
                        return {"success": True, "status": "waiting"}
                    elif "expired" in error_msg or "invalid" in error_msg:
                        return {"success": True, "status": "expired"}
                    else:
                        return {"success": True, "status": "waiting"}
            
            result = await loop.run_in_executor(None, _check_status)
            return result
            
        except Exception as e:
            logger.error(f"❌ 检查二维码状态失败: {e}")
            return {
                "success": False,
                "status": "error",
                "message": str(e)
            }
    
    async def get_user_info(self, cookies: str) -> Optional[Dict[str, Any]]:
        """
        获取用户信息
        
        Args:
            cookies: 115网盘cookies字符串
            
        Returns:
            用户信息字典或None
        """
        try:
            loop = asyncio.get_event_loop()
            
            def _get_info():
                """使用p115client获取用户信息"""
                try:
                    # 解析cookies字符串为字典
                    cookie_dict = {}
                    for item in cookies.split(';'):
                        item = item.strip()
                        if '=' in item:
                            key, value = item.split('=', 1)
                            cookie_dict[key.strip()] = value.strip()
                    
                    # 创建P115Client实例
                    client = P115Client(cookie_dict, check_for_relogin=False)
                    
                    # 获取用户信息
                    result = client.user_info()
                    
                    if result and result.get('state') and result.get('data'):
                        data = result['data']
                        
                        # 解析VIP等级
                        is_vip_value = data.get('is_vip', 0)
                        # is_vip: 0=普通用户, 1-9=不同VIP等级
                        is_vip = bool(is_vip_value and is_vip_value > 0)
                        vip_name = VIP_LEVEL_NAMES.get(is_vip_value, f'VIP{is_vip_value}')
                        
                        user_info = {
                            'user_id': data.get('user_id'),
                            'user_name': data.get('user_name'),
                            'email': data.get('pub_email_mask', ''),
                            'mobile': data.get('pub_mobile_mask', ''),
                            'is_vip': is_vip,
                            'vip_level': is_vip_value,
                            'vip_name': vip_name,
                            'face': {
                                'face_l': data.get('user_face'),
                                'face_m': data.get('user_face'),
                                'face_s': data.get('user_face')
                            },
                            'gender': data.get('gender_show', ''),
                        }
                        
                        # 尝试获取空间信息和VIP到期时间
                        try:
                            # 获取空间信息
                            space_info = client.fs_space_info()
                            if space_info and space_info.get('state'):
                                space_data = space_info.get('data', {})
                                total = space_data.get('all_total', {}).get('size', 0)
                                used = space_data.get('all_use', {}).get('size', 0)
                                # 计算剩余空间：总空间 - 已用空间
                                remain = max(0, total - used)
                                
                                user_info['space'] = {
                                    'total': total,
                                    'used': used,
                                    'remain': remain,
                                }
                                logger.info(f"📊 空间信息 - 总: {total/1024/1024/1024:.2f}GB, 已用: {used/1024/1024/1024:.2f}GB, 剩余: {remain/1024/1024/1024:.2f}GB")
                        except Exception as e:
                            logger.warning(f"⚠️ 获取空间信息失败: {e}")
                        
                        return user_info
                    return None
                except Exception as e:
                    logger.error(f"❌ 获取用户信息失败: {e}")
                    return None
            
            result = await loop.run_in_executor(None, _get_info)
            return result
            
        except Exception as e:
            logger.error(f"❌ 获取用户信息异常: {e}")
            return None
    
    async def upload_file(
        self, 
        cookies: str,
        file_path: str,
        target_dir: str = "/",
        file_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        上传文件到115网盘
        
        Args:
            cookies: 115网盘cookies
            file_path: 本地文件路径
            target_dir: 目标目录路径（如 /Telegram媒体/photo/2025/10/11）
            file_name: 自定义文件名（可选）
            
        Returns:
            {
                "success": bool,
                "pickcode": str,  # 文件ID
                "file_name": str,
                "is_quick": bool,  # 是否秒传
                "message": str
            }
        """
        try:
            loop = asyncio.get_event_loop()
            
            def _upload():
                # 创建P115Client实例
                cookie_dict = {}
                for item in cookies.split(';'):
                    item = item.strip()
                    if '=' in item:
                        key, value = item.split('=', 1)
                        cookie_dict[key.strip()] = value.strip()
                
                logger.info(f"🔑 Cookie字段: {list(cookie_dict.keys())}")
                logger.info(f"🔑 Cookie完整内容: {cookies[:200]}...")  # 只打印前200字符
                
                client = P115Client(cookie_dict, check_for_relogin=False)
                
                # 测试登录状态
                try:
                    user_info = client.user_info()
                    logger.info(f"👤 用户信息验证成功: {user_info.get('user_name', 'Unknown')}")
                except Exception as e:
                    logger.error(f"❌ 用户信息验证失败: {e}")
                    raise Exception(f"115网盘认证失败，请重新登录: {e}")
                
                # 确保目标目录存在
                parent_id = self._ensure_remote_path_static(client, target_dir)
                
                # 上传文件
                upload_name = file_name if file_name else Path(file_path).name
                
                # 检查文件是否存在和可读
                if not os.path.exists(file_path):
                    raise Exception(f"文件不存在: {file_path}")
                if not os.path.isfile(file_path):
                    raise Exception(f"不是文件: {file_path}")
                if not os.access(file_path, os.R_OK):
                    raise Exception(f"文件不可读: {file_path}")
                
                file_size = os.path.getsize(file_path)
                logger.info(f"📤 开始上传: file={file_path}, size={file_size/1024/1024:.2f}MB, pid={parent_id}, filename={upload_name}")
                logger.info(f"📝 文件检查: exists={os.path.exists(file_path)}, readable={os.access(file_path, os.R_OK)}, size={file_size}")
                
                # 尝试上传，如果失败则重试一次
                max_retries = 2
                result = None
                for retry in range(max_retries):
                    try:
                        if retry > 0:
                            logger.info(f"🔄 重试上传 ({retry}/{max_retries-1})...")
                            import time
                            time.sleep(1)  # 等待1秒后重试
                        
                        result = client.upload_file(
                            file=file_path,
                            pid=parent_id,
                            filename=upload_name
                        )
                        
                        logger.info(f"📤 上传完成，返回结果: {result}")
                        
                        # 检查上传是否成功
                        if result.get('state', False):
                            break  # 成功则跳出重试循环
                        else:
                            error_msg = result.get('message', '上传失败')
                            error_code = result.get('code', 'unknown')
                            if retry < max_retries - 1:
                                logger.warning(f"⚠️ 上传失败: {error_msg}, code={error_code}, 准备重试...")
                            else:
                                logger.error(f"❌ 115网盘上传失败（已重试{max_retries}次）: {error_msg}, code={error_code}")
                                return {
                                    "success": False,
                                    "message": f"{error_msg} (已重试{max_retries}次)"
                                }
                    except Exception as upload_error:
                        if retry < max_retries - 1:
                            logger.warning(f"⚠️ 上传异常: {upload_error}, 准备重试...")
                        else:
                            raise
                
                # 最终检查
                if not result or not result.get('state', False):
                    return {
                        "success": False,
                        "message": result.get('message', '上传失败') if result else '上传失败'
                    }
                
                # 判断是否秒传
                is_quick = result.get('status') == 2 and result.get('statuscode') == 0
                
                return {
                    "success": True,
                    "pickcode": result.get('pickcode', ''),
                    "file_name": upload_name,
                    "is_quick": is_quick,
                    "message": "上传成功"
                }
            
            result = await loop.run_in_executor(None, _upload)
            if result.get('success'):
                logger.info(f"📤 文件上传成功: {result['file_name']}")
            else:
                logger.warning(f"⚠️ 文件上传失败: {result.get('message', '未知错误')}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 文件上传失败: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    async def list_files(self, parent_id: str = "0") -> Dict[str, Any]:
        """
        列出目录文件
        
        Args:
            parent_id: 父目录ID
            
        Returns:
            {
                "success": bool,
                "files": List[Dict],
                "folders": List[Dict]
            }
        """
        try:
            if not self.client:
                return {
                    "success": False,
                    "message": "未登录115网盘"
                }
            
            loop = asyncio.get_event_loop()
            
            def _list():
                # 使用 fs_files 获取文件列表
                result = self.client.fs_files({'cid': parent_id, 'limit': 1150})
                data = result.get('data', [])
                
                files = []
                folders = []
                
                for item in data:
                    # 检查是否是目录：没有fid字段的是目录
                    if item.get('fid'):  # 是文件
                        files.append({
                            "id": item.get('fid'),
                            "name": item.get('n', ''),
                            "size": item.get('s', 0),
                            "path": item.get('n', '')
                        })
                    else:  # 是目录
                        folders.append({
                            "id": item.get('cid'),
                            "name": item.get('n', ''),
                            "path": item.get('n', '')
                        })
                
                return {
                    "success": True,
                    "files": files,
                    "folders": folders
                }
            
            return await loop.run_in_executor(None, _list)
            
        except Exception as e:
            logger.error(f"❌ 列出文件失败: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def _format_cookies(self, cookies: Dict[str, str]) -> str:
        """
        将cookies字典格式化为字符串
        
        Args:
            cookies: cookies字典
            
        Returns:
            格式化的cookies字符串 (UID=xxx; CID=xxx; SEID=xxx)
        """
        return "; ".join([f"{k}={v}" for k, v in cookies.items()])
    
    @staticmethod
    def _ensure_remote_path_static(client: P115Client, remote_path: str) -> str:
        """
        确保远程路径存在，不存在则创建（静态方法）
        
        Args:
            client: P115Client实例
            remote_path: 远程路径 (例如: /downloads/videos)
            
        Returns:
            最终目录的ID
        """
        if not remote_path or remote_path == '/':
            return "0"
        
        # 移除首尾的斜杠，使用115的路径格式
        path = remote_path.strip('/')
        
        # 使用 fs_makedirs_app 一次性创建整个路径
        # payload参数可以是字符串（路径）或字典
        logger.info(f"📁 创建115目录: path={path}")
        result = client.fs_makedirs_app(path, pid='0')
        logger.info(f"📁 创建结果: {result}")
        
        # 返回创建的目录ID
        if result.get('state'):
            # 成功时返回 cid 字段（fs_makedirs_app 返回的是 cid）
            dir_id = str(result.get('cid', result.get('id', '0')))
            logger.info(f"✅ 目录创建成功，ID: {dir_id}")
            return dir_id
        else:
            # 失败时可能是目录已存在，需要查找
            # 使用 fs_dir_getid 获取目录ID
            logger.warning(f"⚠️ 目录创建失败，尝试查找: {result}")
            dir_result = client.fs_dir_getid(remote_path)
            logger.info(f"📁 查找结果: {dir_result}")
            # fs_dir_getid 也可能返回 cid
            dir_id = str(dir_result.get('cid', dir_result.get('id', '0')))
            logger.info(f"📁 最终目录ID: {dir_id}")
            return dir_id
    
    def _ensure_remote_path(self, remote_path: str) -> str:
        """
        确保远程路径存在，不存在则创建（实例方法）
        
        Args:
            remote_path: 远程路径 (例如: /downloads/videos)
            
        Returns:
            最终目录的ID
        """
        return self._ensure_remote_path_static(self.client, remote_path)
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.client is not None and hasattr(self.client, 'cookies')


# 全局单例（可选）
_p115_service_instance: Optional[P115Service] = None


def get_p115_service(cookies: Optional[str] = None) -> P115Service:
    """
    获取P115Service实例（单例模式）
    
    Args:
        cookies: 115登录cookies
        
    Returns:
        P115Service实例
    """
    global _p115_service_instance
    
    if cookies:
        _p115_service_instance = P115Service(cookies=cookies)
    elif _p115_service_instance is None:
        _p115_service_instance = P115Service()
    
    return _p115_service_instance

