"""
115网盘 Open API 客户端
基于官方文档: https://www.yuque.com/115yun/open/fd7fidbgsritauxm
"""
import httpx
import hashlib
import time
import os
import base64
import secrets
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from log_manager import get_logger

logger = get_logger('pan115')

# VIP等级名称映射（参考 p115_service.py.backup）
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


class Pan115Client:
    """115网盘 Open API 客户端（同时支持常规登录）"""
    
    def __init__(self, app_id: str, app_key: str, user_id: str, user_key: str, use_proxy: bool = False):
        """
        初始化115网盘客户端
        
        Args:
            app_id: 应用ID (开放平台AppID)
            app_key: 应用密钥 (开放平台AppSecret)
            user_id: 用户ID
            user_key: 用户密钥（可以是cookies字符串或access_token）
            use_proxy: 是否使用系统代理(默认False,因为115是国内服务)
        """
        self.app_id = app_id
        self.app_key = app_key
        self.user_id = user_id
        self.user_key = user_key
        self.use_proxy = use_proxy  # 是否使用代理
        self.base_url = "https://proapi.115.com"  # 开放平台API
        self.open_api_url = "https://passportapi.115.com"  # 开放平台API(正确域名)
        self.auth_url = "https://passportapi.115.com"  # 认证API使用不同的域名
        self.webapi_url = "https://webapi.115.com"  # 常规 Web API
        self.access_token = None  # Bearer Token(用于开放平台API)
    
    def _get_client_kwargs(self, timeout: float = 10.0, **extra_kwargs) -> Dict[str, Any]:
        """
        获取httpx.AsyncClient的参数配置
        
        Args:
            timeout: 超时时间(秒)
            **extra_kwargs: 其他额外参数
        
        Returns:
            客户端配置字典
        """
        kwargs = {'timeout': timeout}
        kwargs.update(extra_kwargs)
        
        if self.use_proxy:
            kwargs['trust_env'] = True  # 使用环境变量中的代理
        else:
            kwargs['trust_env'] = False
            kwargs['proxies'] = None  # 明确禁用所有代理
        
        return kwargs
        
    def _generate_pkce_pair(self) -> tuple[str, str]:
        """
        生成PKCE所需的code_verifier和code_challenge
        
        Returns:
            (code_verifier, code_challenge)
        """
        # 生成code_verifier: 43-128个字符的随机字符串
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # 生成code_challenge: code_verifier的SHA256哈希的base64编码
        challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    async def get_device_code(self) -> Dict[str, Any]:
        """
        获取设备授权码(Device Code Flow第一步)
        
        Returns:
            {
                'success': bool,
                'device_code': str,
                'user_code': str,
                'verification_uri': str,
                'expires_in': int,
                'interval': int,
                'code_verifier': str,  # 用于后续获取token
                'message': str
            }
        """
        try:
            if not self.app_id:
                return {
                    'success': False,
                    'message': '未配置AppID'
                }
            
            # 生成PKCE参数
            code_verifier, code_challenge = self._generate_pkce_pair()
            
            # 准备请求参数
            params = {
                'client_id': self.app_id,
                'code_challenge': code_challenge,
                'code_challenge_method': 'sha256',  # 115要求小写
                'scope': 'basic'  # 基础权限
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            # 如果有cookies,也带上(可能有帮助)
            if self.user_key:
                headers['Cookie'] = self.user_key
            
            logger.info(f"🔑 请求设备授权码: client_id={self.app_id}")
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0)) as client:
                response = await client.post(
                    f"{self.open_api_url}/open/authDeviceCode",
                    data=params,
                    headers=headers
                )
                
                logger.info(f"📥 设备授权码响应: status={response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"📦 设备授权码数据: {result}")
                    
                    if result.get('state') == 1 or result.get('code') == 0:
                        data = result.get('data', result)
                        
                        # 115返回的是二维码格式,需要适配
                        # 返回的数据: uid, time, qrcode(URL), sign
                        uid = data.get('uid')
                        qrcode_url = data.get('qrcode')
                        
                        if uid and qrcode_url:
                            logger.info(f"✅ 获取到开放平台授权二维码: uid={uid}")
                            
                            # 115的实现：返回二维码让用户扫描，扫描后自动授权开放平台
                            return {
                                'success': True,
                                'device_code': uid,  # 二维码token的uid
                                'user_code': '',  # 不需要手动输入码
                                'verification_uri': qrcode_url,  # 二维码URL，前端用QRCode组件显示
                                'qrcode_token': data,  # 完整的二维码token数据
                                'expires_in': 300,  # 默认5分钟
                                'interval': 2,  # 2秒轮询一次（检查扫码状态）
                                'code_verifier': code_verifier,
                                'message': '请使用115 APP扫描二维码完成开放平台授权'
                            }
                    
                    error_msg = result.get('error', result.get('message', '获取授权信息失败'))
                    logger.warning(f"⚠️ 授权信息获取失败: {error_msg}")
                    return {
                        'success': False,
                        'message': error_msg or '返回数据格式不正确'
                    }
                else:
                    error_text = response.text[:200]
                    logger.error(f"❌ 设备授权码请求失败: HTTP {response.status_code}, {error_text}")
                    return {
                        'success': False,
                        'message': f'HTTP错误: {response.status_code}'
                    }
                    
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else repr(e)
            logger.error(f"❌ 获取设备授权码异常: {error_type}: {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"{error_type}: {error_msg}"
            }
    
    async def poll_device_token(self, device_code: str, code_verifier: str, qrcode_token: Dict = None, max_attempts: int = 1, interval: int = 0) -> Dict[str, Any]:
        """
        轮询检查扫码状态并获取访问令牌
        
        115的流程：
        1. 先检查二维码扫描状态
        2. 扫描成功后，使用新的cookies + AppID获取access_token
        
        Args:
            device_code: 二维码uid
            code_verifier: PKCE验证码(暂未使用)
            qrcode_token: 完整的二维码token数据
            max_attempts: 最大轮询次数(默认1,由前端控制轮询)
            interval: 轮询间隔(秒,默认0)
            
        Returns:
            {
                'success': bool,
                'access_token': str,
                'refresh_token': str,
                'expires_in': int,
                'status': 'pending'|'authorized'|'error',
                'message': str
            }
        """
        try:
            # 步骤1: 检查二维码扫描状态（使用已有的check_regular_qrcode_status方法）
            if not qrcode_token:
                qrcode_token = {
                    'uid': device_code,
                    'time': int(time.time()),
                    'sign': ''
                }
            
            logger.info(f"🔄 检查扫码状态: uid={device_code}")
            
            # 检查扫码状态（可能会超时，需要捕获异常）
            try:
                status_result = await self.check_regular_qrcode_status(qrcode_token, 'qandroid')
            except Exception as check_err:
                # 检查扫码状态时出错（可能是超时），返回pending继续等待
                logger.warning(f"⚠️ 检查扫码状态出错: {check_err}, 继续等待...")
                return {
                    'success': False,
                    'status': 'pending',
                    'message': '正在检查扫码状态...'
                }
            
            if not status_result.get('success'):
                # 还在等待扫码
                return {
                    'success': False,
                    'status': 'pending',
                    'message': '等待用户扫码...'
                }
            
            # 步骤2: 扫码成功，获取到新的cookies
            status = status_result.get('status')
            
            if status == 'confirmed':
                # 扫码确认成功，获取到新的cookies
                new_cookies = status_result.get('user_key', '')
                new_user_id = status_result.get('user_id', '')
                
                logger.info(f"✅ 扫码成功，获取到新凭证: user_id={new_user_id}")
                
                # 更新客户端的cookies
                self.user_key = new_cookies
                self.user_id = new_user_id
                
                # 纯Cookie模式：扫码登录只获取Cookie，不自动激活开放平台
                # 如果用户需要开放平台API，需要后续手动调用 activate_open_api()
                logger.info(f"✅ 扫码登录完成（Cookie模式）")
                
                return {
                    'success': True,
                    'status': 'authorized',
                    'user_key': new_cookies,
                    'user_id': new_user_id,
                    'message': '扫码登录成功'
                }
                        
            elif status == 'waiting':
                return {
                    'success': False,
                    'status': 'pending',
                    'message': '等待用户扫码...'
                }
            elif status == 'scanned':
                return {
                    'success': False,
                    'status': 'pending',
                    'message': '已扫码，等待用户确认...'
                }
            elif status == 'expired':
                return {
                    'success': False,
                    'status': 'expired',
                    'message': '二维码已过期'
                }
            else:
                return {
                    'success': False,
                    'status': 'error',
                    'message': status_result.get('message', '未知状态')
                }
                    
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else repr(e)
            logger.error(f"❌ 轮询异常: {error_type}: {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'status': 'error',
                'message': f"{error_type}: {error_msg}"
            }
    
    async def get_access_token(self) -> Dict[str, Any]:
        """
        使用cookies + AppID + AppSecret获取115开放平台access_token
        
        需要：
        1. 已登录的cookies（通过扫码登录获得）
        2. 开放平台AppID（从115开放平台申请）
        3. 开放平台AppSecret（从115开放平台申请）
        
        Returns:
            {
                'success': bool,
                'access_token': str,
                'refresh_token': str,
                'expires_in': int,
                'message': str
            }
        """
        try:
            if not self.app_id:
                logger.warning("⚠️ 未配置AppID")
                return {
                    'success': False,
                    'message': '未配置开放平台AppID，请先在115开放平台申请应用'
                }
            
            if not self.app_key:
                logger.warning("⚠️ 未配置AppSecret")
                return {
                    'success': False,
                    'message': '未配置开放平台AppSecret，请在设置中填写'
                }
            
            if not self.user_key:
                logger.warning("⚠️ 未配置cookies")
                return {
                    'success': False,
                    'message': '请先扫码登录115账号'
                }
            
            logger.info(f"🔑 使用cookies + AppID + AppSecret获取access_token")
            logger.info(f"📝 AppID: {self.app_id}")
            logger.info(f"🔐 AppSecret: {self.app_key[:4]}...{self.app_key[-4:] if len(self.app_key) > 8 else '***'}")
            
            # 准备请求参数（需要签名）
            timestamp = str(int(time.time()))
            params = {
                'client_id': self.app_id,
                'timestamp': timestamp,
            }
            
            # 生成签名（使用AppSecret）
            params['sign'] = self._generate_signature(params)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            # 115 Open API的token端点
            token_url = f"{self.open_api_url}/app/1.0/token"
            
            logger.info(f"🔄 请求access_token: {token_url}")
            logger.info(f"📦 请求参数: {params}")
            logger.info(f"🍪 Cookies长度: {len(self.user_key)} 字符")
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0, follow_redirects=False)) as client:
                response = await client.post(
                    token_url,
                    data=params,  # 使用form-data，包含签名
                    headers=headers
                )
                
                logger.info(f"📥 响应: HTTP {response.status_code}")
                
                if response.status_code == 302:
                    redirect_url = response.headers.get('Location', 'N/A')
                    logger.warning(f"🔀 重定向到: {redirect_url}")
                    logger.error(f"❌ Cookies无效或已过期，需要重新登录")
                    return {
                        'success': False,
                        'message': '登录凭证已过期，请重新扫码登录'
                    }
                
                logger.info(f"📄 响应内容: {response.text[:500]}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"📦 数据: {result}")
                    
                    if result.get('state') == 1 or result.get('code') == 0:
                        data = result.get('data', result)
                        access_token = data.get('access_token')
                        
                        if access_token:
                            self.access_token = access_token
                            logger.info(f"✅ access_token获取成功!")
                            
                            return {
                                'success': True,
                                'access_token': access_token,
                                'refresh_token': data.get('refresh_token', ''),
                                'expires_in': data.get('expires_in', 7200),
                                'message': 'access_token获取成功'
                            }
                        else:
                            error_msg = result.get('message', result.get('error', '响应中没有access_token'))
                            logger.error(f"❌ {error_msg}")
                            return {'success': False, 'message': error_msg}
                    else:
                        error_msg = result.get('message', result.get('error', 'API返回失败'))
                        error_code = result.get('code', result.get('errno', 'unknown'))
                        logger.error(f"❌ {error_msg} (code={error_code})")
                        
                        # 提供更详细的错误信息
                        if 'signature' in error_msg.lower() or 'sign' in error_msg.lower():
                            error_msg = f"签名验证失败，请检查AppSecret是否正确。原始错误：{error_msg}"
                        elif 'client_id' in error_msg.lower():
                            error_msg = f"AppID无效，请检查AppID是否正确。原始错误：{error_msg}"
                        
                        return {'success': False, 'message': error_msg}
                elif response.status_code == 401:
                    return {'success': False, 'message': 'AppID或AppSecret错误，请检查配置'}
                elif response.status_code == 403:
                    return {'success': False, 'message': '没有权限访问开放平台API，请检查应用状态'}
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.error(f"❌ {error_msg}")
                    return {'success': False, 'message': error_msg}
                    
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else repr(e)
            logger.error(f"❌ 获取access_token异常: {error_type}: {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"{error_type}: {error_msg}"
            }
        
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """生成API签名"""
        # 按key排序
        sorted_params = sorted(params.items())
        # 拼接字符串
        param_str = ''.join([f"{k}{v}" for k, v in sorted_params])
        # 添加app_key（如果存在）
        if self.app_key:
            sign_str = param_str + self.app_key
        else:
            # 某些API（如二维码登录）可能不需要app_key
            sign_str = param_str
        # MD5签名
        return hashlib.md5(sign_str.encode()).hexdigest().upper()
    
    async def get_upload_info(self, file_path: str, target_dir_id: str = "0") -> Dict[str, Any]:
        """
        获取上传信息
        
        Args:
            file_path: 本地文件路径
            target_dir_id: 目标目录ID，0表示根目录
            
        Returns:
            包含上传URL和参数的字典
        """
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # 计算文件SHA1
            sha1 = hashlib.sha1()
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(8192)
                    if not data:
                        break
                    sha1.update(data)
            file_sha1 = sha1.hexdigest().upper()
            
            logger.info(f"📊 文件信息: {file_name}, 大小: {file_size}, SHA1: {file_sha1}")
            
            # 构建请求参数
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'file_name': file_name,
                'file_size': str(file_size),
                'file_sha1': file_sha1,
                'target': target_dir_id,
            }
            
            # 生成签名
            params['sign'] = self._generate_signature(params)
            
            # 请求上传信息
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.base_url}/2.0/upload/init",
                    data=params
                )
            
            logger.info(f"📥 获取上传信息响应: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 上传信息: {result}")
                
                if result.get('state') == True or result.get('code') == 0:
                    return {
                        'success': True,
                        'data': result.get('data', result),
                        'file_sha1': file_sha1
                    }
                else:
                    error_msg = result.get('message', result.get('error', '未知错误'))
                    return {
                        'success': False,
                        'message': f"获取上传信息失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            logger.error(f"❌ 获取上传信息异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def upload_file(self, file_path: str, target_dir_id: str = "0",
                         target_path: Optional[str] = None) -> Dict[str, Any]:
        """
        上传文件到115网盘
        
        自动检测使用开放平台API或Web API
        
        Args:
            file_path: 本地文件路径
            target_dir_id: 目标目录ID，0表示根目录
            target_path: 目标路径（如果提供，会先创建目录）
            
        Returns:
            {"success": bool, "message": str, "file_id": str, "quick_upload": bool}
        """
        try:
            # 判断是否为Cookie认证
            is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
            
            # 如果提供了路径，先创建目录
            if target_path and target_path != '/':
                dir_result = await self.create_directory_path(target_path)
                if dir_result['success']:
                    target_dir_id = dir_result['dir_id']
                else:
                    logger.warning(f"⚠️ 创建目录失败: {dir_result['message']}")
            
            if is_cookie_auth and not self.app_id:
                # 使用Web API上传
                return await self._upload_file_web_api(file_path, target_dir_id)
            
            # 使用开放平台API上传
            # 获取上传信息
            upload_info = await self.get_upload_info(file_path, target_dir_id)
            
            if not upload_info['success']:
                return upload_info
            
            data = upload_info['data']
            
            # 检查是否已存在（秒传）
            if data.get('status') == 2 or data.get('pick_code'):
                logger.info(f"✅ 文件已存在，秒传成功")
                return {
                    'success': True,
                    'message': '文件秒传成功',
                    'file_id': data.get('file_id', ''),
                    'quick_upload': True
                }
            
            # 需要真实上传
            upload_url = data.get('upload_url') or data.get('host')
            if not upload_url:
                return {
                    'success': False,
                    'message': '未获取到上传URL'
                }
            
            logger.info(f"📤 开始上传文件到: {upload_url}")
            
            # 构建上传请求
            file_name = os.path.basename(file_path)
            
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_name, f, 'application/octet-stream')
                }
                
                # 上传参数
                upload_params = {
                    'app_id': self.app_id,
                    'user_id': self.user_id,
                    'user_key': self.user_key,
                    'timestamp': str(int(time.time())),
                    'target': target_dir_id,
                }
                
                # 添加上传信息中的其他参数
                if 'upload_params' in data:
                    upload_params.update(data['upload_params'])
                
                # 生成签名
                upload_params['sign'] = self._generate_signature(upload_params)
                
                async with httpx.AsyncClient(**self._get_client_kwargs(timeout=600.0)) as client:
                    response = await client.post(
                        upload_url,
                        files=files,
                        data=upload_params
                    )
            
            logger.info(f"📥 上传响应: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 上传结果: {result}")
                
                if result.get('state') == True or result.get('code') == 0:
                    file_id = result.get('data', {}).get('file_id', result.get('file_id', ''))
                    logger.info(f"✅ 文件上传成功，file_id: {file_id}")
                    return {
                        'success': True,
                        'message': '文件上传成功',
                        'file_id': file_id,
                        'quick_upload': False
                    }
                else:
                    error_msg = result.get('message', result.get('error', '未知错误'))
                    return {
                        'success': False,
                        'message': f"上传失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"上传失败: HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 上传文件异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def _upload_file_web_api(self, file_path: str, target_dir_id: str = "0") -> Dict[str, Any]:
        """
        使用Web API上传文件（Cookie认证）
        
        适用于没有开放平台AppID的场景
        注意：Web API上传较复杂，这里提供基础实现
        """
        try:
            import hashlib
            
            # 计算文件SHA1
            sha1 = hashlib.sha1()
            file_size = 0
            file_name = os.path.basename(file_path)
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    sha1.update(chunk)
                    file_size += len(chunk)
            
            file_sha1 = sha1.hexdigest().upper()
            logger.info(f"📝 文件信息: {file_name}, size={file_size}, sha1={file_sha1}")
            
            # 先尝试秒传
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json',
            }
            
            # 检查文件是否已存在（秒传）
            check_data = {
                'file_id': target_dir_id,
                'file_name': file_name,
                'file_size': file_size,
                'file_sha1': file_sha1,
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                check_response = await client.post(
                    f"{self.webapi_url}/files/add",
                    data=check_data,
                    headers=headers
                )
            
            if check_response.status_code == 200:
                result = check_response.json()
                logger.info(f"📦 Web API检查响应: {result}")
                
                if result.get('state'):
                    # 秒传成功
                    file_id = result.get('file_id', result.get('data', {}).get('file_id', ''))
                    logger.info(f"✅ Web API秒传成功")
                    return {
                        'success': True,
                        'message': '文件秒传成功',
                        'file_id': file_id,
                        'quick_upload': True
                    }
            
            # 需要真实上传
            logger.warning("⚠️ Web API真实上传功能尚未完整实现")
            logger.warning("⚠️ 建议配置开放平台AppID以使用完整上传功能")
            
            return {
                'success': False,
                'message': 'Web API上传需要更复杂的实现，建议配置开放平台AppID'
            }
                
        except Exception as e:
            logger.error(f"❌ Web API上传文件异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def create_directory_path(self, path: str, parent_id: str = "0") -> Dict[str, Any]:
        """
        创建目录路径（递归创建）
        
        自动检测使用开放平台API或Web API
        
        Args:
            path: 目录路径，如 /Media/Photos/2024
            parent_id: 父目录ID
            
        Returns:
            {"success": bool, "dir_id": str, "message": str}
        """
        try:
            # 清理路径
            path = path.strip('/')
            if not path:
                return {'success': True, 'dir_id': parent_id}
            
            # 分割路径
            parts = path.split('/')
            current_parent_id = parent_id
            
            for part in parts:
                if not part:
                    continue
                
                # 创建目录（会自动选择API）
                result = await self.create_directory(part, current_parent_id)
                if not result['success']:
                    return result
                
                current_parent_id = result['dir_id']
            
            return {
                'success': True,
                'dir_id': current_parent_id,
                'message': f"目录创建成功: {path}"
            }
            
        except Exception as e:
            logger.error(f"❌ 创建目录路径异常: {e}")
            return {'success': False, 'dir_id': parent_id, 'message': str(e)}
    
    async def create_directory(self, dir_name: str, parent_id: str = "0") -> Dict[str, Any]:
        """
        创建单个目录
        
        自动检测使用开放平台API或Web API
        
        Args:
            dir_name: 目录名称
            parent_id: 父目录ID，0表示根目录
            
        Returns:
            {"success": bool, "dir_id": str}
        """
        try:
            # 判断是否为Cookie认证
            is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
            
            if is_cookie_auth and not self.app_id:
                # 使用Web API
                return await self._create_directory_web_api(dir_name, parent_id)
            
            # 使用开放平台API
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'cname': dir_name,
                'pid': parent_id,
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.base_url}/2.0/file/add",
                    data=params
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('state') == True or result.get('code') == 0:
                    dir_id = result.get('data', {}).get('cid', result.get('cid', parent_id))
                    logger.info(f"✅ 目录创建成功: {dir_name} (ID: {dir_id})")
                    return {
                        'success': True,
                        'dir_id': str(dir_id)
                    }
                elif '已存在' in result.get('message', '') or result.get('code') == 20004:
                    # 目录已存在，查询目录ID
                    logger.info(f"📁 目录已存在: {dir_name}")
                    list_result = await self.list_files(parent_id, limit=100)
                    if list_result['success']:
                        for item in list_result['files']:
                            if item['is_dir'] and item['name'] == dir_name:
                                return {
                                    'success': True,
                                    'dir_id': item['id']
                                }
                    return {
                        'success': True,
                        'dir_id': parent_id  # 返回父目录ID
                    }
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'dir_id': parent_id,
                        'message': f"创建目录失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'dir_id': parent_id,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 创建目录异常: {e}")
            return {'success': False, 'dir_id': parent_id, 'message': str(e)}
    
    async def _create_directory_web_api(self, dir_name: str, parent_id: str = "0") -> Dict[str, Any]:
        """
        使用Web API创建目录（Cookie认证）
        
        适用于没有开放平台AppID的场景
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json',
            }
            
            data = {
                'pid': parent_id,
                'cname': dir_name,
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.webapi_url}/files/add",
                    data=data,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Web API创建目录响应: {result}")
                
                if result.get('state'):
                    dir_id = result.get('cid', result.get('data', {}).get('cid', parent_id))
                    logger.info(f"✅ Web API目录创建成功: {dir_name} (ID: {dir_id})")
                    return {
                        'success': True,
                        'dir_id': str(dir_id)
                    }
                elif '已存在' in str(result.get('error', '')):
                    # 目录已存在，查询目录ID
                    logger.info(f"📁 目录已存在: {dir_name}")
                    list_result = await self._list_files_web_api(parent_id, limit=100)
                    if list_result['success']:
                        for item in list_result['files']:
                            if item['is_dir'] and item['name'] == dir_name:
                                return {
                                    'success': True,
                                    'dir_id': item['id']
                                }
                    return {
                        'success': True,
                        'dir_id': parent_id
                    }
                else:
                    error_msg = result.get('error', '未知错误')
                    return {
                        'success': False,
                        'dir_id': parent_id,
                        'message': f"创建目录失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'dir_id': parent_id,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Web API创建目录异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'dir_id': parent_id, 'message': str(e)}
    
    async def get_qrcode_token(self) -> Dict[str, Any]:
        """
        获取115登录二维码token
        
        Returns:
            {"success": bool, "qrcode_token": str, "qrcode_url": str, "expires_in": int}
        """
        try:
            # 115开放平台二维码登录API端点
            # 参考文档: https://www.yuque.com/115yun/open/okr2cq0wywelscpe
            # 注意：二维码登录API可能不需要签名（因为还没有user_id和user_key）
            timestamp = str(int(time.time()))
            params = {
                'app_id': self.app_id,
                'timestamp': timestamp,
            }
            
            # 添加必要的请求头以避免被115的防盗链拦截
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://115.com/',
                'Origin': 'https://115.com'
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0, follow_redirects=False)) as client:
                # 115开放平台二维码登录 - 正确的API端点
                # 参考: https://www.yuque.com/115yun/open/okr2cq0wywelscpe
                response = await client.get(
                    f"{self.auth_url}/app/1.0/{self.app_id}/1.0/qrcode/get",
                    params=params,
                    headers=headers
                )
            
            logger.info(f"📥 获取二维码响应: {response.status_code}")
            logger.info(f"📥 响应头: {dict(response.headers)}")
            logger.info(f"📥 响应内容: {response.text[:500]}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 二维码数据: {result}")
                
                if result.get('state') == True or result.get('code') == 0:
                    data = result.get('data', {})
                    qrcode_token = data.get('uid') or data.get('qrcode_token') or data.get('token')
                    
                    # 生成二维码URL
                    qrcode_url = data.get('qrcode_url') or f"https://qrcodeapi.115.com/api/1.0/web/1.0/qrcode?uid={qrcode_token}"
                    
                    return {
                        'success': True,
                        'qrcode_token': qrcode_token,
                        'qrcode_url': qrcode_url,
                        'expires_in': data.get('expires_in', 300)  # 默认5分钟过期
                    }
                else:
                    error_msg = result.get('message', result.get('error', '未知错误'))
                    return {
                        'success': False,
                        'message': f"获取二维码失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            logger.error(f"❌ 获取二维码异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def check_qrcode_status(self, qrcode_token: str) -> Dict[str, Any]:
        """
        检查二维码扫码状态
        
        Args:
            qrcode_token: 二维码token
            
        Returns:
            {"success": bool, "status": str, "user_id": str, "user_key": str}
            status: waiting(等待扫码)/scanned(已扫码)/confirmed(已确认)/expired(已过期)
        """
        try:
            params = {
                'app_id': self.app_id,
                'qrcode_token': qrcode_token,
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0)) as client:
                # 115开放平台二维码状态查询
                # 参考: https://www.yuque.com/115yun/open/okr2cq0wywelscpe
                response = await client.get(
                    f"{self.auth_url}/app/1.0/{self.app_id}/1.0/qrcode/status",
                    params={'uid': qrcode_token}
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('state') == True or result.get('code') == 0:
                    data = result.get('data', {})
                    status = data.get('status', 'waiting')
                    
                    response_data = {
                        'success': True,
                        'status': status,
                    }
                    
                    # 如果已确认，返回用户凭据
                    if status == 'confirmed':
                        response_data['user_id'] = data.get('user_id', '')
                        response_data['user_key'] = data.get('user_key', '')
                        logger.info(f"✅ 用户已确认登录: user_id={data.get('user_id')}")
                    
                    return response_data
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'status': 'error',
                        'message': error_msg
                    }
            else:
                return {
                    'success': False,
                    'status': 'error',
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 检查二维码状态异常: {e}")
            return {
                'success': False,
                'status': 'error',
                'message': str(e)
            }
    
    async def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息和空间信息
        
        支持两种方式：
        1. Open API 方式（需要 app_id, user_id, user_key）
        2. 常规登录方式（使用 cookies，user_key 存储的是 cookies）
        
        Returns:
            {
                "success": bool,
                "user_info": {
                    "user_id": str,
                    "user_name": str,
                    "email": str,
                    "is_vip": bool,
                    "vip_level": int,
                    "space": {
                        "total": int,  # 总空间（字节）
                        "used": int,   # 已用空间（字节）
                        "remain": int  # 剩余空间（字节）
                    }
                },
                "message": str
            }
        """
        try:
            # 判断是否为常规登录（cookies 包含 UID=, CID=, SEID=）
            is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
            
            if is_cookie_auth:
                # 使用常规 Web API 获取用户信息
                return await self._get_user_info_by_cookie()
            
            # 使用 Open API 获取用户信息
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0)) as client:
                response = await client.post(
                    f"{self.base_url}/2.0/user/info",
                    data=params
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 用户信息响应: {result}")
                
                if result.get('state') == True or result.get('code') == 0:
                    data = result.get('data', {})
                    
                    # 解析用户信息
                    vip_data = data.get('vip', {})
                    vip_level = vip_data.get('level', 0)
                    is_vip = bool(vip_data.get('is_vip', 0))
                    vip_name = VIP_LEVEL_NAMES.get(vip_level, f'VIP{vip_level}' if is_vip else '普通用户')
                    
                    user_info = {
                        'user_id': data.get('user_id', self.user_id),
                        'user_name': data.get('user_name', ''),
                        'email': data.get('email', ''),
                        'is_vip': is_vip,
                        'vip_level': vip_level,
                        'vip_name': vip_name,
                    }
                    
                    # 解析空间信息
                    space_data = data.get('space', {})
                    if space_data:
                        user_info['space'] = {
                            'total': int(space_data.get('all_total', {}).get('size', 0)),
                            'used': int(space_data.get('all_use', {}).get('size', 0)),
                            'remain': int(space_data.get('all_remain', {}).get('size', 0)),
                        }
                    else:
                        # 如果没有空间信息，尝试单独获取
                        user_info['space'] = {
                            'total': 0,
                            'used': 0,
                            'remain': 0,
                        }
                    
                    return {
                        'success': True,
                        'user_info': user_info,
                        'message': '获取用户信息成功'
                    }
                else:
                    return {
                        'success': False,
                        'message': f"获取用户信息失败: {result.get('message', '未知错误')}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            logger.error(f"❌ 获取用户信息异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"获取用户信息异常: {str(e)}"
            }
    
    async def _get_user_info_by_cookie(self) -> Dict[str, Any]:
        """
        使用 cookies 获取用户信息（常规登录方式）
        
        直接使用专用的空间信息API（参考 p115_service.py.backup）
        
        Returns:
            与 get_user_info 相同的格式
        """
        try:
            # 直接使用专用的空间信息 API
            space_result = await self._get_space_info_only()
            
            user_info = {
                'user_id': self.user_id,
                'user_name': '',  # Cookie方式无法获取用户名（需要从登录响应中保存）
                'email': '',
                'is_vip': False,  # Cookie方式无法获取VIP信息（需要从登录响应中保存）
                'vip_level': 0,
                'vip_name': '普通用户',
                'space': space_result.get('space', {'total': 0, 'used': 0, 'remain': 0})
            }
            
            if space_result.get('success'):
                logger.info(f"✅ Cookie方式获取用户信息成功")
                return {
                    'success': True,
                    'user_info': user_info,
                    'message': '获取用户信息成功'
                }
            else:
                logger.warning(f"⚠️ 获取空间信息失败: {space_result.get('message')}")
                return {
                    'success': True,  # 仍返回成功，但空间信息为0
                    'user_info': user_info,
                    'message': f"已登录，但无法获取空间信息: {space_result.get('message')}"
                }
                
        except Exception as e:
            logger.error(f"❌ 使用Cookie获取用户信息异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"获取用户信息异常: {str(e)}"
            }
    
    async def _get_space_info_only(self) -> Dict[str, Any]:
        """
        仅获取空间信息（用于登录后立即获取）
        
        优先使用p115client SDK的fs_space_info()方法(最可靠)
        如果SDK不可用,则回退到115云开放平台的Web API
        
        Returns:
            {
                "success": bool,
                "space": {"total": int, "used": int, "remain": int},
                "message": str
            }
        """
        # 方案0: 优先使用p115client官方库(最可靠)
        try:
            from services.p115client_wrapper import get_space_info_with_p115client, P115CLIENT_AVAILABLE
            
            if P115CLIENT_AVAILABLE:
                logger.info("🚀 尝试使用p115client官方库获取空间信息")
                p115_result = await get_space_info_with_p115client(self.user_key)
                
                if p115_result.get('success'):
                    logger.info(f"✅ p115client成功获取空间信息")
                    return p115_result
                else:
                    logger.warning(f"⚠️ p115client获取失败: {p115_result.get('message')}")
            else:
                logger.info("📦 p115client库不可用,跳过")
        except Exception as p115_error:
            logger.warning(f"⚠️ p115client调用异常: {p115_error}")
        
        # 方案1: 使用115开放平台API(需要access_token)
        # 如果有AppID,先尝试获取access_token,然后调用开放平台API
        if self.app_id and not self.access_token:
            logger.info("🔑 检测到AppID,尝试获取access_token")
            token_result = await self.get_access_token()
            if token_result.get('success'):
                self.access_token = token_result.get('access_token')
                logger.info("✅ access_token获取成功,将使用开放平台API")
        
        # 如果有access_token,使用开放平台API
        if self.access_token:
            try:
                headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                }
                
                async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0)) as client:
                    # 调用开放平台用户信息API
                    response = await client.get(
                        f"{self.open_api_url}/open/user/info",
                        headers=headers
                    )
                    
                    logger.info(f"📦 开放平台API响应: status={response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"📦 开放平台API完整响应: {str(result)[:800]}")
                        
                        if result.get('state') or result.get('success'):
                            data = result.get('data', result)
                            
                            # 解析空间信息
                            space_info = data.get('space_info', data.get('space', {}))
                            total = 0
                            used = 0
                            remain = 0
                            
                            if isinstance(space_info, dict):
                                # 尝试多种数据结构
                                if 'all_total' in space_info:
                                    if isinstance(space_info['all_total'], dict):
                                        total = int(space_info['all_total'].get('size', 0))
                                        used = int(space_info.get('all_use', {}).get('size', 0))
                                    else:
                                        total = int(space_info.get('all_total', 0))
                                        used = int(space_info.get('all_use', 0))
                                elif 'total' in space_info:
                                    total = int(space_info.get('total', 0))
                                    used = int(space_info.get('used', 0))
                                
                                remain = max(0, total - used)
                            
                            if total > 0:
                                logger.info(f"✅ 开放平台API获取空间信息成功: 总={total/1024/1024/1024:.2f}GB, 已用={used/1024/1024/1024:.2f}GB")
                                return {
                                    'success': True,
                                    'space': {'total': total, 'used': used, 'remain': remain},
                                    'message': '从115开放平台获取空间信息成功'
                                }
                            else:
                                logger.warning(f"⚠️ 开放平台API返回的空间信息为0")
                        else:
                            error_msg = result.get('error', result.get('message', 'Unknown'))
                            logger.warning(f"⚠️ 开放平台API失败: {error_msg}")
                    else:
                        logger.warning(f"⚠️ 开放平台API HTTP错误: {response.status_code}")
                        
            except Exception as open_api_error:
                logger.warning(f"⚠️ 开放平台API调用失败: {open_api_error}")
        
        # 方案1: 回退到Web API(大概率会失败,因为有严格限流)
        logger.info("📡 回退到Web API(可能会因限流失败)")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://115.com/',
                'Origin': 'https://115.com',
                'X-Requested-With': 'XMLHttpRequest',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0, follow_redirects=True)) as client:
                # 方案1: 尝试多个不同的API获取空间信息
                # 参考: https://www.yuque.com/115yun/open/ot1litggzxa1czww
                
                # 1.1 先尝试 /user/info (基础用户信息API)
                try:
                    user_info_response = await client.get(
                        f"{self.webapi_url}/user/info",
                        headers=headers
                    )
                    
                    logger.info(f"📦 /user/info API响应: status={user_info_response.status_code}")
                    
                    if user_info_response.status_code == 200:
                        user_info_result = user_info_response.json()
                        logger.info(f"📦 /user/info完整响应(前800字符): {str(user_info_result)[:800]}")
                        logger.info(f"📦 /user/info响应keys: {list(user_info_result.keys())}")
                        
                        if user_info_result.get('state'):
                            data = user_info_result.get('data', {})
                            logger.info(f"📦 data字段keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                            
                            # 根据115云开放平台文档,空间信息在data字段中
                            total = 0
                            used = 0
                            remain = 0
                            
                            # 尝试多种可能的数据结构
                            # 结构1: data.space_info.all_total.size
                            space_info = data.get('space_info', {})
                            if isinstance(space_info, dict) and space_info:
                                logger.info(f"📦 space_info字段: {space_info}")
                                if isinstance(space_info.get('all_total'), dict):
                                    total = int(space_info['all_total'].get('size', 0))
                                    used = int(space_info.get('all_use', {}).get('size', 0))
                                    remain = int(space_info.get('all_remain', {}).get('size', 0))
                                elif isinstance(space_info.get('all_total'), (int, float)):
                                    total = int(space_info.get('all_total', 0))
                                    used = int(space_info.get('all_use', 0))
                                    remain = int(space_info.get('all_remain', 0))
                            
                            # 结构2: 直接从data中获取
                            if total == 0:
                                if isinstance(data.get('all_total'), dict):
                                    total = int(data['all_total'].get('size', 0))
                                    used = int(data.get('all_use', {}).get('size', 0))
                                    remain = int(data.get('all_remain', {}).get('size', 0))
                                elif isinstance(data.get('all_total'), (int, float)):
                                    total = int(data.get('all_total', 0))
                                    used = int(data.get('all_use', 0))
                                    remain = int(data.get('all_remain', 0))
                            
                            # 如果remain为0但total和used有值,计算remain
                            if remain == 0 and total > 0:
                                remain = max(0, total - used)
                            
                            logger.info(f"📊 解析结果: total={total}, used={used}, remain={remain}")
                            
                            if total > 0:  # 成功获取到空间信息
                                logger.info(f"✅ 从/user/data获取空间信息成功: 总={total/1024/1024/1024:.2f}GB, 已用={used/1024/1024/1024:.2f}GB, 剩余={remain/1024/1024/1024:.2f}GB")
                                return {
                                    'success': True,
                                    'space': {'total': total, 'used': used, 'remain': remain},
                                    'message': '从用户数据获取空间信息成功'
                                }
                            else:
                                logger.warning(f"⚠️ /user/data API返回的空间信息为0")
                        else:
                            logger.warning(f"⚠️ /user/info API state=False: {user_info_result.get('error', 'Unknown error')}")
                except Exception as user_info_error:
                    logger.warning(f"⚠️ /user/info API调用失败: {user_info_error}")
                
                # 方案2: 回退到 /files API
                try:
                    files_response = await client.get(
                        f"{self.webapi_url}/files",
                        params={'cid': 0, 'limit': 1},
                        headers=headers
                    )
                    
                    if files_response.status_code == 200:
                        files_result = files_response.json()
                        if files_result.get('state'):
                            space_data = files_result.get('space', {})
                            if space_data:
                                total = 0
                                used = 0
                                remain = 0
                                
                                if isinstance(space_data.get('all_total'), dict):
                                    total = int(space_data['all_total'].get('size', 0))
                                    used = int(space_data.get('all_use', {}).get('size', 0))
                                    remain = int(space_data.get('all_remain', {}).get('size', 0))
                                elif isinstance(space_data.get('all_total'), (int, float)):
                                    total = int(space_data.get('all_total', 0))
                                    used = int(space_data.get('all_use', 0))
                                    remain = int(space_data.get('all_remain', 0))
                                
                                if remain == 0 and total > 0:
                                    remain = max(0, total - used)
                                
                                if total > 0:
                                    logger.info(f"✅ 从/files获取空间信息成功: 总={total/1024/1024/1024:.2f}GB")
                                    return {
                                        'success': True,
                                        'space': {'total': total, 'used': used, 'remain': remain},
                                        'message': '从文件列表获取空间信息成功'
                                    }
                except Exception as files_error:
                    logger.warning(f"⚠️ /files API调用失败: {files_error}")
                
                # 所有方案都失败
                logger.warning(f"⚠️ 所有空间信息API都失败")
                return {
                    'success': False,
                    'space': {'total': 0, 'used': 0, 'remain': 0},
                    'message': '所有空间信息API都失败'
                }
                
        except Exception as e:
            logger.error(f"❌ 获取空间信息异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'space': {'total': 0, 'used': 0, 'remain': 0},
                'message': str(e)
            }
    
    async def list_files(self, parent_id: str = "0", limit: int = 1150, 
                        offset: int = 0, show_dir: int = 1) -> Dict[str, Any]:
        """
        列出目录下的文件和文件夹
        
        自动检测使用开放平台API或Web API
        
        Args:
            parent_id: 父目录ID，0表示根目录
            limit: 返回数量限制
            offset: 偏移量
            show_dir: 是否显示文件夹，1=显示，0=不显示
            
        Returns:
            {
                "success": bool,
                "files": [
                    {
                        "id": str,
                        "name": str,
                        "size": int,
                        "is_dir": bool,
                        "ctime": int,  # 创建时间戳
                        "utime": int,  # 修改时间戳
                    }
                ],
                "count": int,
                "message": str
            }
        """
        try:
            # 判断是否为Cookie认证
            is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
            
            if is_cookie_auth and not self.app_id:
                # 使用Web API
                return await self._list_files_web_api(parent_id, limit, offset, show_dir)
            
            # 使用开放平台API
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'cid': parent_id,
                'limit': str(limit),
                'offset': str(offset),
                'show_dir': str(show_dir),
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.get(
                    f"{self.base_url}/2.0/file/list",
                    params=params
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 文件列表响应状态: state={result.get('state')}, count={result.get('count', 0)}")
                
                if result.get('state') == True or result.get('code') == 0:
                    data = result.get('data', [])
                    
                    files = []
                    for item in data:
                        file_info = {
                            'id': item.get('fid') or item.get('cid', ''),
                            'name': item.get('n', ''),
                            'size': int(item.get('s', 0)),
                            'is_dir': bool(item.get('cid') and not item.get('fid')),
                            'ctime': int(item.get('te', 0)),
                            'utime': int(item.get('tu', 0)),
                        }
                        files.append(file_info)
                    
                    return {
                        'success': True,
                        'files': files,
                        'count': result.get('count', len(files)),
                        'message': f'获取文件列表成功，共 {len(files)} 项'
                    }
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'files': [],
                        'count': 0,
                        'message': f"获取文件列表失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'files': [],
                    'count': 0,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 列出文件异常: {e}")
            return {
                'success': False,
                'files': [],
                'count': 0,
                'message': str(e)
            }
    
    async def _list_files_web_api(self, parent_id: str = "0", limit: int = 1150,
                                  offset: int = 0, show_dir: int = 1) -> Dict[str, Any]:
        """
        使用Web API列出文件（Cookie认证）
        
        适用于没有开放平台AppID的场景
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json',
            }
            
            params = {
                'cid': parent_id,
                'limit': limit,
                'offset': offset,
                'show_dir': show_dir,
                'o': 'user_ptime',  # 排序方式
                'asc': 0,  # 降序
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.get(
                    f"{self.webapi_url}/files",
                    params=params,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Web API文件列表: state={result.get('state')}, count={result.get('count', 0)}")
                
                if result.get('state'):
                    data = result.get('data', [])
                    
                    files = []
                    for item in data:
                        file_info = {
                            'id': item.get('fid') or item.get('cid', ''),
                            'name': item.get('n', ''),
                            'size': int(item.get('s', 0)),
                            'is_dir': bool(item.get('cid') and not item.get('fid')),
                            'ctime': int(item.get('te', 0)),
                            'utime': int(item.get('tu', 0)),
                            'pick_code': item.get('pc', ''),  # 提取码
                            'sha1': item.get('sha', ''),  # 文件SHA1
                        }
                        files.append(file_info)
                    
                    return {
                        'success': True,
                        'files': files,
                        'count': result.get('count', len(files)),
                        'message': f'获取文件列表成功，共 {len(files)} 项'
                    }
                else:
                    error_msg = result.get('error', '未知错误')
                    return {
                        'success': False,
                        'files': [],
                        'count': 0,
                        'message': f"获取文件列表失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'files': [],
                    'count': 0,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Web API列出文件异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'files': [],
                'count': 0,
                'message': str(e)
            }
    
    async def delete_files(self, file_ids: List[str]) -> Dict[str, Any]:
        """
        删除文件或文件夹
        
        自动检测使用开放平台API或Web API
        
        Args:
            file_ids: 文件ID列表（支持批量删除）
            
        Returns:
            {"success": bool, "message": str}
        """
        try:
            # 判断是否为Cookie认证
            is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
            
            if is_cookie_auth and not self.app_id:
                # 使用Web API
                return await self._delete_files_web_api(file_ids)
            
            # 使用开放平台API
            fid_str = ','.join(file_ids)
            
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'fid': fid_str,
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.base_url}/2.0/file/delete",
                    data=params
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('state') == True or result.get('code') == 0:
                    logger.info(f"✅ 删除成功: {len(file_ids)} 个文件/文件夹")
                    return {
                        'success': True,
                        'message': f'成功删除 {len(file_ids)} 个文件/文件夹'
                    }
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'message': f"删除失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 删除文件异常: {e}")
            return {'success': False, 'message': str(e)}
    
    async def _delete_files_web_api(self, file_ids: List[str]) -> Dict[str, Any]:
        """
        使用Web API删除文件（Cookie认证）
        
        适用于没有开放平台AppID的场景
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json',
            }
            
            # Web API使用 fid[0]=xxx&fid[1]=yyy 格式
            data = {}
            for idx, fid in enumerate(file_ids):
                data[f'fid[{idx}]'] = fid
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.webapi_url}/rb/delete",
                    data=data,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Web API删除响应: {result}")
                
                if result.get('state'):
                    logger.info(f"✅ Web API删除成功: {len(file_ids)} 个文件/文件夹")
                    return {
                        'success': True,
                        'message': f'成功删除 {len(file_ids)} 个文件/文件夹'
                    }
                else:
                    error_msg = result.get('error', '未知错误')
                    return {
                        'success': False,
                        'message': f"删除失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Web API删除文件异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def move_files(self, file_ids: List[str], target_dir_id: str) -> Dict[str, Any]:
        """
        移动文件或文件夹
        
        自动检测使用开放平台API或Web API
        
        Args:
            file_ids: 要移动的文件ID列表
            target_dir_id: 目标目录ID
            
        Returns:
            {"success": bool, "message": str}
        """
        try:
            # 判断是否为Cookie认证
            is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
            
            if is_cookie_auth and not self.app_id:
                # 使用Web API
                return await self._move_files_web_api(file_ids, target_dir_id)
            
            # 使用开放平台API
            fid_str = ','.join(file_ids)
            
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'fid': fid_str,
                'pid': target_dir_id,
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.base_url}/2.0/file/move",
                    data=params
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('state') == True or result.get('code') == 0:
                    logger.info(f"✅ 移动成功: {len(file_ids)} 个文件/文件夹")
                    return {
                        'success': True,
                        'message': f'成功移动 {len(file_ids)} 个文件/文件夹'
                    }
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'message': f"移动失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 移动文件异常: {e}")
            return {'success': False, 'message': str(e)}
    
    async def _move_files_web_api(self, file_ids: List[str], target_dir_id: str) -> Dict[str, Any]:
        """
        使用Web API移动文件（Cookie认证）
        
        适用于没有开放平台AppID的场景
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json',
            }
            
            # Web API使用 fid[0]=xxx&fid[1]=yyy 格式
            data = {'pid': target_dir_id}
            for idx, fid in enumerate(file_ids):
                data[f'fid[{idx}]'] = fid
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.webapi_url}/files/move",
                    data=data,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Web API移动响应: {result}")
                
                if result.get('state'):
                    logger.info(f"✅ Web API移动成功: {len(file_ids)} 个文件/文件夹")
                    return {
                        'success': True,
                        'message': f'成功移动 {len(file_ids)} 个文件/文件夹'
                    }
                else:
                    error_msg = result.get('error', '未知错误')
                    return {
                        'success': False,
                        'message': f"移动失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Web API移动文件异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def copy_files(self, file_ids: List[str], target_dir_id: str) -> Dict[str, Any]:
        """
        复制文件或文件夹
        
        自动检测使用开放平台API或Web API
        
        Args:
            file_ids: 要复制的文件ID列表
            target_dir_id: 目标目录ID
            
        Returns:
            {"success": bool, "message": str}
        """
        try:
            # 判断是否为Cookie认证
            is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
            
            if is_cookie_auth and not self.app_id:
                # 使用Web API
                return await self._copy_files_web_api(file_ids, target_dir_id)
            
            # 使用开放平台API
            fid_str = ','.join(file_ids)
            
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'fid': fid_str,
                'pid': target_dir_id,
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.base_url}/2.0/file/copy",
                    data=params
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('state') == True or result.get('code') == 0:
                    logger.info(f"✅ 复制成功: {len(file_ids)} 个文件/文件夹")
                    return {
                        'success': True,
                        'message': f'成功复制 {len(file_ids)} 个文件/文件夹'
                    }
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'message': f"复制失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 复制文件异常: {e}")
            return {'success': False, 'message': str(e)}
    
    async def _copy_files_web_api(self, file_ids: List[str], target_dir_id: str) -> Dict[str, Any]:
        """
        使用Web API复制文件（Cookie认证）
        
        适用于没有开放平台AppID的场景
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json',
            }
            
            # Web API使用 fid[0]=xxx&fid[1]=yyy 格式
            data = {'pid': target_dir_id}
            for idx, fid in enumerate(file_ids):
                data[f'fid[{idx}]'] = fid
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.webapi_url}/files/copy",
                    data=data,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Web API复制响应: {result}")
                
                if result.get('state'):
                    logger.info(f"✅ Web API复制成功: {len(file_ids)} 个文件/文件夹")
                    return {
                        'success': True,
                        'message': f'成功复制 {len(file_ids)} 个文件/文件夹'
                    }
                else:
                    error_msg = result.get('error', '未知错误')
                    return {
                        'success': False,
                        'message': f"复制失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Web API复制文件异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def rename_file(self, file_id: str, new_name: str) -> Dict[str, Any]:
        """
        重命名文件或文件夹
        
        自动检测使用开放平台API或Web API
        
        Args:
            file_id: 文件或文件夹ID
            new_name: 新名称
            
        Returns:
            {"success": bool, "message": str}
        """
        try:
            # 判断是否为Cookie认证
            is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
            
            if is_cookie_auth and not self.app_id:
                # 使用Web API
                return await self._rename_file_web_api(file_id, new_name)
            
            # 使用开放平台API
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'fid': file_id,
                'file_name': new_name,
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.base_url}/2.0/file/edit",
                    data=params
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('state') == True or result.get('code') == 0:
                    logger.info(f"✅ 重命名成功: {new_name}")
                    return {
                        'success': True,
                        'message': f'重命名成功: {new_name}'
                    }
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'message': f"重命名失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 重命名文件异常: {e}")
            return {'success': False, 'message': str(e)}
    
    async def _rename_file_web_api(self, file_id: str, new_name: str) -> Dict[str, Any]:
        """
        使用Web API重命名文件（Cookie认证）
        
        适用于没有开放平台AppID的场景
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json',
            }
            
            data = {
                'fid': file_id,
                'file_name': new_name,
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.webapi_url}/files/edit",
                    data=data,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Web API重命名响应: {result}")
                
                if result.get('state'):
                    logger.info(f"✅ Web API重命名成功: {new_name}")
                    return {
                        'success': True,
                        'message': f'重命名成功: {new_name}'
                    }
                else:
                    error_msg = result.get('error', '未知错误')
                    return {
                        'success': False,
                        'message': f"重命名失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Web API重命名文件异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        获取文件或文件夹详细信息
        
        Args:
            file_id: 文件或文件夹ID
            
        Returns:
            {
                "success": bool,
                "file_info": {
                    "id": str,
                    "name": str,
                    "size": int,
                    "is_dir": bool,
                    "ctime": int,
                    "utime": int,
                    "parent_id": str,
                },
                "message": str
            }
        """
        try:
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'file_id': file_id,
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0)) as client:
                response = await client.get(
                    f"{self.base_url}/2.0/file/info",
                    params=params
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('state') == True or result.get('code') == 0:
                    data = result.get('data', {})
                    
                    file_info = {
                        'id': data.get('fid') or data.get('cid', ''),
                        'name': data.get('n', ''),
                        'size': int(data.get('s', 0)),
                        'is_dir': bool(data.get('cid') and not data.get('fid')),
                        'ctime': int(data.get('te', 0)),
                        'utime': int(data.get('tu', 0)),
                        'parent_id': str(data.get('pid', '0')),
                    }
                    
                    return {
                        'success': True,
                        'file_info': file_info,
                        'message': '获取文件信息成功'
                    }
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'message': f"获取文件信息失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 获取文件信息异常: {e}")
            return {'success': False, 'message': str(e)}
    
    async def search_files(self, keyword: str, parent_id: str = "0", 
                          file_type: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """
        搜索文件
        
        Args:
            keyword: 搜索关键词
            parent_id: 搜索范围的父目录ID，0表示全盘搜索
            file_type: 文件类型过滤，可选值：
                - None: 所有类型
                - "video": 视频
                - "audio": 音频
                - "image": 图片
                - "document": 文档
            limit: 返回数量限制
            
        Returns:
            {
                "success": bool,
                "files": [...],
                "count": int,
                "message": str
            }
        """
        try:
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'search_value': keyword,
                'cid': parent_id,
                'limit': str(limit),
                'offset': '0',
            }
            
            if file_type:
                # 文件类型映射
                type_map = {
                    'video': '1',
                    'audio': '2',
                    'image': '3',
                    'document': '4',
                }
                params['type'] = type_map.get(file_type, '0')
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.get(
                    f"{self.base_url}/2.0/file/search",
                    params=params
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('state') == True or result.get('code') == 0:
                    data = result.get('data', [])
                    
                    files = []
                    for item in data:
                        file_info = {
                            'id': item.get('fid') or item.get('cid', ''),
                            'name': item.get('n', ''),
                            'size': int(item.get('s', 0)),
                            'is_dir': bool(item.get('cid') and not item.get('fid')),
                            'ctime': int(item.get('te', 0)),
                            'utime': int(item.get('tu', 0)),
                            'parent_id': str(item.get('pid', '0')),
                        }
                        files.append(file_info)
                    
                    return {
                        'success': True,
                        'files': files,
                        'count': len(files),
                        'message': f'搜索成功，找到 {len(files)} 个结果'
                    }
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'files': [],
                        'count': 0,
                        'message': f"搜索失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'files': [],
                    'count': 0,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 搜索文件异常: {e}")
            return {
                'success': False,
                'files': [],
                'count': 0,
                'message': str(e)
            }
    
    async def get_download_url(self, file_id: str, user_agent: Optional[str] = None) -> Dict[str, Any]:
        """
        获取文件下载链接
        
        自动检测使用开放平台API或Web API
        
        Args:
            file_id: 文件ID（pickcode）
            user_agent: 自定义 User-Agent
            
        Returns:
            {
                "success": bool,
                "download_url": str,
                "file_name": str,
                "file_size": int,
                "message": str
            }
        """
        try:
            # 判断是否为Cookie认证
            is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
            
            if is_cookie_auth and not self.app_id:
                # 使用Web API
                return await self._get_download_url_web_api(file_id, user_agent)
            
            # 使用开放平台API
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'pick_code': file_id,
            }
            
            params['sign'] = self._generate_signature(params)
            
            headers = {}
            if user_agent:
                headers['User-Agent'] = user_agent
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0)) as client:
                response = await client.get(
                    f"{self.base_url}/2.0/file/download_url",
                    params=params,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('state') == True or result.get('code') == 0:
                    data = result.get('data', {})
                    
                    return {
                        'success': True,
                        'download_url': data.get('url', {}).get('url', ''),
                        'file_name': data.get('file_name', ''),
                        'file_size': int(data.get('file_size', 0)),
                        'message': '获取下载链接成功'
                    }
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'message': f"获取下载链接失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 获取下载链接异常: {e}")
            return {'success': False, 'message': str(e)}
    
    async def _get_download_url_web_api(self, pick_code: str, user_agent: Optional[str] = None) -> Dict[str, Any]:
        """
        使用Web API获取文件下载链接（Cookie认证）
        
        适用于没有开放平台AppID的场景
        """
        try:
            headers = {
                'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json',
            }
            
            data = {
                'pickcode': pick_code,
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0)) as client:
                response = await client.post(
                    f"{self.webapi_url}/files/download",
                    data=data,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Web API下载链接响应: {result}")
                
                if result.get('state'):
                    data = result.get('data', result)
                    file_url = data.get('url', {})
                    
                    # url可能是字典或字符串
                    if isinstance(file_url, dict):
                        download_url = file_url.get('url', '')
                    else:
                        download_url = file_url
                    
                    return {
                        'success': True,
                        'download_url': download_url,
                        'file_name': data.get('file_name', ''),
                        'file_size': int(data.get('file_size', 0)),
                        'message': '获取下载链接成功'
                    }
                else:
                    error_msg = result.get('error', '未知错误')
                    return {
                        'success': False,
                        'message': f"获取下载链接失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Web API获取下载链接异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def save_share(self, share_code: str, receive_code: Optional[str] = None, 
                        target_dir_id: str = "0", file_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        转存115分享链接到我的网盘
        
        Args:
            share_code: 分享码（从分享链接中提取，如 https://115.com/s/sw1abc123 中的 sw1abc123）
            receive_code: 提取码/接收码（如果分享有密码保护）
            target_dir_id: 目标目录ID（默认为根目录）
            file_ids: 要转存的文件ID列表（如果为空，则转存全部）
            
        Returns:
            {
                "success": bool,
                "message": str,
                "saved_count": int,  # 成功转存的文件数量
                "file_list": [...]   # 转存的文件列表
            }
        """
        try:
            logger.info(f"📥 开始转存分享: share_code={share_code}, receive_code={'***' if receive_code else None}")
            
            # 构建请求参数
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'share_code': share_code,
                'receive_code': receive_code or '',
                'cid': target_dir_id,
            }
            
            # 如果指定了文件ID，添加到参数中
            if file_ids:
                params['file_id'] = ','.join(file_ids)
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=60.0)) as client:
                response = await client.post(
                    f"{self.base_url}/2.0/share/receive",
                    data=params
                )
            
            logger.info(f"📥 转存响应: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 转存结果: {result}")
                
                if result.get('state') == True or result.get('code') == 0:
                    data = result.get('data', {})
                    
                    # 提取转存结果
                    saved_count = data.get('count', 0)
                    file_list = data.get('file_list', [])
                    
                    logger.info(f"✅ 转存成功: {saved_count} 个文件")
                    
                    return {
                        'success': True,
                        'message': f'成功转存 {saved_count} 个文件',
                        'saved_count': saved_count,
                        'file_list': file_list
                    }
                else:
                    error_msg = result.get('message', result.get('error', '未知错误'))
                    error_code = result.get('code', 'unknown')
                    
                    # 处理常见错误
                    if 'password' in error_msg.lower() or error_code == 20009:
                        error_msg = "提取码错误或分享链接需要提取码"
                    elif 'not found' in error_msg.lower() or error_code == 20010:
                        error_msg = "分享链接不存在或已失效"
                    elif 'expired' in error_msg.lower() or error_code == 20011:
                        error_msg = "分享链接已过期"
                    
                    logger.error(f"❌ 转存失败: {error_msg} (code={error_code})")
                    
                    return {
                        'success': False,
                        'message': f"转存失败: {error_msg}",
                        'saved_count': 0,
                        'file_list': []
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}: {response.text[:200]}",
                    'saved_count': 0,
                    'file_list': []
                }
                
        except Exception as e:
            logger.error(f"❌ 转存分享异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"转存异常: {str(e)}",
                'saved_count': 0,
                'file_list': []
            }
    
    async def get_share_info(self, share_code: str, receive_code: Optional[str] = None) -> Dict[str, Any]:
        """
        获取115分享链接的文件信息（转存前预览）
        
        Args:
            share_code: 分享码
            receive_code: 提取码/接收码
            
        Returns:
            {
                "success": bool,
                "share_info": {
                    "title": str,
                    "file_count": int,
                    "files": [...]
                },
                "message": str
            }
        """
        try:
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'share_code': share_code,
                'receive_code': receive_code or '',
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0)) as client:
                response = await client.get(
                    f"{self.base_url}/2.0/share/info",
                    params=params
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('state') == True or result.get('code') == 0:
                    data = result.get('data', {})
                    
                    share_info = {
                        'title': data.get('share_title', ''),
                        'file_count': data.get('file_count', 0),
                        'files': data.get('file_list', []),
                        'expire_time': data.get('expire_time', 0),
                    }
                    
                    return {
                        'success': True,
                        'share_info': share_info,
                        'message': '获取分享信息成功'
                    }
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'message': f"获取分享信息失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 获取分享信息异常: {e}")
            return {'success': False, 'message': str(e)}
    
    # ==================== 离线下载功能 ====================
    
    async def add_offline_task(self, url: str, target_dir_id: str = "0") -> Dict[str, Any]:
        """
        添加离线下载任务
        
        自动检测使用开放平台API或Web API
        
        Args:
            url: 下载链接（支持HTTP/HTTPS/磁力链接/BT种子URL）
            target_dir_id: 目标目录ID，默认为根目录
            
        Returns:
            {
                "success": bool,
                "task_id": str,  # 任务ID
                "message": str
            }
        """
        try:
            # 判断是否为Cookie认证
            is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
            
            if is_cookie_auth and not self.app_id:
                # 使用Web API
                return await self._add_offline_task_web_api(url, target_dir_id)
            
            # 使用开放平台API
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'url': url,
                'wp_path_id': target_dir_id,
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.base_url}/2.0/offline/add_task",
                    data=params
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 添加离线任务响应: {result}")
                
                if result.get('state') == True or result.get('code') == 0:
                    data = result.get('data', {})
                    task_id = data.get('info_hash', '') or data.get('task_id', '')
                    
                    logger.info(f"✅ 离线任务添加成功: task_id={task_id}")
                    return {
                        'success': True,
                        'task_id': task_id,
                        'message': '离线任务添加成功'
                    }
                else:
                    error_msg = result.get('message', result.get('error', '未知错误'))
                    error_code = result.get('code', 'unknown')
                    
                    # 处理常见错误
                    if 'url' in error_msg.lower() or error_code == 911:
                        error_msg = "下载链接无效或不支持"
                    elif 'quota' in error_msg.lower() or error_code == 10008:
                        error_msg = "离线任务数量已达上限"
                    elif 'exists' in error_msg.lower():
                        error_msg = "任务已存在"
                    
                    logger.error(f"❌ 添加离线任务失败: {error_msg} (code={error_code})")
                    return {
                        'success': False,
                        'message': error_msg
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 添加离线任务异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def _add_offline_task_web_api(self, url: str, target_dir_id: str = "0") -> Dict[str, Any]:
        """
        使用Web API添加离线下载任务（Cookie认证）
        
        适用于没有开放平台AppID的场景
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json',
            }
            
            data = {
                'url': url,
                'wp_path_id': target_dir_id,
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.webapi_url}/lixian/add",
                    data=data,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Web API添加离线任务响应: {result}")
                
                if result.get('state'):
                    task_id = result.get('info_hash', '') or result.get('id', '')
                    logger.info(f"✅ Web API离线任务添加成功: task_id={task_id}")
                    return {
                        'success': True,
                        'task_id': task_id,
                        'message': '离线任务添加成功'
                    }
                else:
                    error_msg = result.get('error', result.get('error_msg', '未知错误'))
                    return {
                        'success': False,
                        'message': f"添加离线任务失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Web API添加离线任务异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def get_offline_tasks(self, page: int = 1) -> Dict[str, Any]:
        """
        获取离线任务列表
        
        自动检测使用开放平台API或Web API
        
        Args:
            page: 页码，从1开始
            
        Returns:
            {
                "success": bool,
                "tasks": [
                    {
                        "task_id": str,
                        "name": str,
                        "status": int,  # 0=下载中, 1=已完成, 2=失败, -1=等待中
                        "status_text": str,
                        "size": int,
                        "percentDone": float,
                        "add_time": int,
                        "file_id": str,
                    }
                ],
                "count": int,
                "message": str
            }
        """
        try:
            # 判断是否为Cookie认证
            is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
            
            if is_cookie_auth and not self.app_id:
                # 使用Web API
                return await self._get_offline_tasks_web_api(page)
            
            # 使用开放平台API
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'page': str(page),
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0)) as client:
                response = await client.get(
                    f"{self.base_url}/2.0/offline/list",
                    params=params
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 离线任务列表响应: count={result.get('data', {}).get('count', 0)}")
                
                if result.get('state') == True or result.get('code') == 0:
                    data = result.get('data', {})
                    tasks_raw = data.get('tasks', [])
                    
                    # 格式化任务信息
                    tasks = []
                    for task in tasks_raw:
                        status = task.get('status', 0)
                        status_text_map = {
                            -1: '等待中',
                            0: '下载中',
                            1: '已完成',
                            2: '失败',
                            4: '已删除'
                        }
                        
                        tasks.append({
                            'task_id': task.get('info_hash', '') or task.get('id', ''),
                            'name': task.get('name', ''),
                            'status': status,
                            'status_text': status_text_map.get(status, '未知'),
                            'size': int(task.get('size', 0)),
                            'percentDone': float(task.get('percentDone', 0)),
                            'add_time': int(task.get('add_time', 0)),
                            'file_id': task.get('file_id', ''),
                        })
                    
                    return {
                        'success': True,
                        'tasks': tasks,
                        'count': len(tasks),
                        'message': f'获取到 {len(tasks)} 个离线任务'
                    }
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'tasks': [],
                        'count': 0,
                        'message': f"获取离线任务失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'tasks': [],
                    'count': 0,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 获取离线任务异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'tasks': [],
                'count': 0,
                'message': str(e)
            }
    
    async def _get_offline_tasks_web_api(self, page: int = 1) -> Dict[str, Any]:
        """
        使用Web API获取离线任务列表（Cookie认证）
        
        适用于没有开放平台AppID的场景
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json',
            }
            
            params = {
                'page': page,
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0)) as client:
                response = await client.get(
                    f"{self.webapi_url}/lixian/task",
                    params=params,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Web API离线任务列表响应: {result}")
                
                if result.get('state'):
                    tasks_raw = result.get('tasks', result.get('data', []))
                    
                    # 格式化任务信息
                    tasks = []
                    for task in tasks_raw:
                        status = task.get('status', 0)
                        status_text_map = {
                            -1: '等待中',
                            0: '下载中',
                            1: '已完成',
                            2: '失败',
                            4: '已删除'
                        }
                        
                        tasks.append({
                            'task_id': task.get('info_hash', '') or task.get('id', ''),
                            'name': task.get('name', ''),
                            'status': status,
                            'status_text': status_text_map.get(status, '未知'),
                            'size': int(task.get('size', 0)),
                            'percentDone': float(task.get('percentDone', 0)),
                            'add_time': int(task.get('add_time', 0)),
                            'file_id': task.get('file_id', ''),
                        })
                    
                    logger.info(f"✅ Web API获取到 {len(tasks)} 个离线任务")
                    return {
                        'success': True,
                        'tasks': tasks,
                        'count': len(tasks),
                        'message': f'获取到 {len(tasks)} 个离线任务'
                    }
                else:
                    error_msg = result.get('error', '未知错误')
                    return {
                        'success': False,
                        'tasks': [],
                        'count': 0,
                        'message': f"获取离线任务失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'tasks': [],
                    'count': 0,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Web API获取离线任务异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'tasks': [],
                'count': 0,
                'message': str(e)
            }
    
    async def delete_offline_task(self, task_ids: List[str]) -> Dict[str, Any]:
        """
        删除离线任务
        
        自动检测使用开放平台API或Web API
        
        Args:
            task_ids: 任务ID列表
            
        Returns:
            {"success": bool, "message": str}
        """
        try:
            # 判断是否为Cookie认证
            is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
            
            if is_cookie_auth and not self.app_id:
                # 使用Web API
                return await self._delete_offline_task_web_api(task_ids)
            
            # 使用开放平台API
            task_ids_str = ','.join(task_ids)
            
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'hash': task_ids_str,
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.base_url}/2.0/offline/delete",
                    data=params
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 删除离线任务响应: {result}")
                
                if result.get('state') == True or result.get('code') == 0:
                    logger.info(f"✅ 成功删除 {len(task_ids)} 个离线任务")
                    return {
                        'success': True,
                        'message': f'成功删除 {len(task_ids)} 个离线任务'
                    }
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'message': f"删除离线任务失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 删除离线任务异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def _delete_offline_task_web_api(self, task_ids: List[str]) -> Dict[str, Any]:
        """
        使用Web API删除离线任务（Cookie认证）
        
        适用于没有开放平台AppID的场景
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json',
            }
            
            # Web API使用 hash[0]=xxx&hash[1]=yyy 格式
            data = {}
            for idx, task_id in enumerate(task_ids):
                data[f'hash[{idx}]'] = task_id
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.webapi_url}/lixian/task_del",
                    data=data,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Web API删除离线任务响应: {result}")
                
                if result.get('state'):
                    logger.info(f"✅ Web API成功删除 {len(task_ids)} 个离线任务")
                    return {
                        'success': True,
                        'message': f'成功删除 {len(task_ids)} 个离线任务'
                    }
                else:
                    error_msg = result.get('error', '未知错误')
                    return {
                        'success': False,
                        'message': f"删除离线任务失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Web API删除离线任务异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def clear_offline_tasks(self, flag: int = 1) -> Dict[str, Any]:
        """
        清空离线任务
        
        自动检测使用开放平台API或Web API
        
        Args:
            flag: 清空标志
                - 0: 清空所有任务
                - 1: 清空已完成任务（默认）
                - 2: 清空失败任务
            
        Returns:
            {"success": bool, "message": str}
        """
        try:
            # 判断是否为Cookie认证
            is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
            
            if is_cookie_auth and not self.app_id:
                # 使用Web API
                return await self._clear_offline_tasks_web_api(flag)
            
            # 使用开放平台API
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'flag': str(flag),
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.base_url}/2.0/offline/clear",
                    data=params
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 清空离线任务响应: {result}")
                
                if result.get('state') == True or result.get('code') == 0:
                    flag_text_map = {0: '所有', 1: '已完成', 2: '失败'}
                    flag_text = flag_text_map.get(flag, '指定')
                    
                    logger.info(f"✅ 成功清空{flag_text}离线任务")
                    return {
                        'success': True,
                        'message': f'成功清空{flag_text}离线任务'
                    }
                else:
                    error_msg = result.get('message', '未知错误')
                    return {
                        'success': False,
                        'message': f"清空离线任务失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 清空离线任务异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def _clear_offline_tasks_web_api(self, flag: int = 1) -> Dict[str, Any]:
        """
        使用Web API清空离线任务（Cookie认证）
        
        适用于没有开放平台AppID的场景
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
                'Accept': 'application/json',
            }
            
            data = {
                'flag': flag,
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.post(
                    f"{self.webapi_url}/lixian/task_clear",
                    data=data,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 Web API清空离线任务响应: {result}")
                
                if result.get('state'):
                    flag_text_map = {0: '所有', 1: '已完成', 2: '失败'}
                    flag_text = flag_text_map.get(flag, '指定')
                    
                    logger.info(f"✅ Web API成功清空{flag_text}离线任务")
                    return {
                        'success': True,
                        'message': f'成功清空{flag_text}离线任务'
                    }
                else:
                    error_msg = result.get('error', '未知错误')
                    return {
                        'success': False,
                        'message': f"清空离线任务失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Web API清空离线任务异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试连接（使用 get_user_info）"""
        result = await self.get_user_info()
        if result['success']:
            return {
                'success': True,
                'message': '115网盘连接成功',
                'user_info': result.get('user_info', {})
            }
        else:
            return {
                'success': False,
                'message': f"连接失败: {result.get('message', '未知错误')}"
            }
    
    # ==================== 常规扫码登录（非 Open API）====================
    
    async def get_regular_qrcode(self, app: str = "web") -> Dict[str, Any]:
        """
        获取115登录二维码（纯Cookie模式）
        
        注意：此方法始终使用常规登录二维码，不管是否配置了AppID
        如果需要使用开放平台API，请在登录后调用 activate_open_api()
        
        Args:
            app: 应用类型，可选值：
                - "web": 网页版（默认）
                - "android": Android客户端
                - "ios": iOS客户端
                - "tv": TV版
                - "alipaymini": 支付宝小程序
                - "wechatmini": 微信小程序
                - "qandroid": 115生活Android版（推荐）
                
        Returns:
            {
                "success": bool,
                "qrcode_url": str,  # 二维码图片URL（base64）
                "qrcode_token": {
                    "uid": str,
                    "time": int,
                    "sign": str
                },
                "expires_in": int,
                "app": str,
                "message": str
            }
        """
        try:
            # 始终使用常规登录二维码（纯Cookie模式）
            # 115 常规登录二维码 API
            # 参考：https://github.com/ChenyangGao/web-mount-packs/tree/main/python-115-client
            # 不同的app类型使用不同的URL路径
            # 格式: https://qrcodeapi.115.com/api/1.0/{app}/1.0/token
            url = f"https://qrcodeapi.115.com/api/1.0/{app}/1.0/token"
            
            logger.info(f"📱 生成常规登录二维码: app={app}, url={url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0, follow_redirects=True)) as client:
                response = await client.get(url, headers=headers)
            
            logger.info(f"📥 常规二维码响应: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📦 二维码数据: {result}")
                
                if result.get('state') or result.get('code') == 0:
                    data = result.get('data', {})
                    
                    # 提取二维码信息
                    qrcode_token = {
                        'uid': data.get('uid', ''),
                        'time': data.get('time', 0),
                        'sign': data.get('sign', ''),
                    }
                    
                    # 二维码图片URL
                    qrcode_url = data.get('qrcode', '')
                    
                    return {
                        'success': True,
                        'qrcode_url': qrcode_url,
                        'qrcode_token': qrcode_token,
                        'expires_in': 300,  # 默认5分钟
                        'app': app,
                        'message': '获取二维码成功'
                    }
                else:
                    error_msg = result.get('message', result.get('error', '未知错误'))
                    return {
                        'success': False,
                        'message': f"获取二维码失败: {error_msg}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            logger.error(f"❌ 获取常规二维码异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    async def check_regular_qrcode_status(self, qrcode_token: Dict[str, Any], app: str = "web") -> Dict[str, Any]:
        """
        检查常规115登录二维码状态
        
        Args:
            qrcode_token: 二维码token数据 {"uid": str, "time": int, "sign": str}
            app: 应用类型（与获取二维码时保持一致）
            
        Returns:
            {
                "success": bool,
                "status": str,  # "waiting" | "scanned" | "confirmed" | "expired"
                "cookies": str,  # 登录成功后的cookies（status=confirmed时返回）
                "user_id": str,  # 用户ID
                "message": str
            }
        """
        try:
            uid = qrcode_token.get('uid', '')
            time_val = qrcode_token.get('time', 0)
            sign = qrcode_token.get('sign', '')
            
            if not all([uid, time_val, sign]):
                return {
                    'success': False,
                    'status': 'error',
                    'message': '二维码token数据不完整'
                }
            
            # 检查扫码状态
            status_url = f"https://qrcodeapi.115.com/get/status/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            
            params = {
                'uid': uid,
                'time': time_val,
                'sign': sign,
            }
            
            # 增加timeout到30秒,因为115的状态检查API可能比较慢
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                logger.info(f"🌐 请求扫码状态API: {status_url}")
                response = await client.get(status_url, params=params, headers=headers)
                logger.info(f"📡 状态API响应: HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📱 扫码状态: {result}")
                
                data = result.get('data', {})
                status_code = data.get('status', 0)
                
                # status: 0=等待扫码, 1=已扫码待确认, 2=已确认
                if status_code == 2:
                    # 已确认，获取登录凭证
                    logger.info(f"✅ 扫码已确认，获取登录凭证")
                    
                    # 请求登录接口获取 cookies
                    # 不同的app类型使用不同的URL路径
                    # 格式: https://passportapi.115.com/app/1.0/{app}/1.0/login/qrcode
                    login_url = f"https://passportapi.115.com/app/1.0/{app}/1.0/login/qrcode"
                    
                    logger.info(f"🔐 登录URL: {login_url}, app={app}")
                    
                    login_params = {
                        'account': uid,
                        'app': app,
                    }
                    
                    async with httpx.AsyncClient(**self._get_client_kwargs(timeout=10.0, follow_redirects=False)) as login_client:
                        login_response = await login_client.post(
                            login_url,
                            data=login_params,
                            headers=headers
                        )
                    
                    logger.info(f"🔐 登录响应: {login_response.status_code}")
                    
                    if login_response.status_code == 200:
                        login_result = login_response.json()
                        logger.info(f"🔐 登录结果: {login_result}")
                        
                        if login_result.get('state'):
                            login_data = login_result.get('data', {})
                            
                            # 提取 cookies
                            cookie_dict = login_data.get('cookie', {})
                            user_id = str(login_data.get('user_id', ''))
                            
                            # 🔑 提取 access_token (根据115开放平台文档,扫码登录响应中包含access_token)
                            access_token = login_data.get('access_token', login_data.get('token', ''))
                            if access_token:
                                logger.info(f"🔑 获取到access_token: {access_token[:30]}...")
                            else:
                                logger.warning(f"⚠️ 登录响应中未找到access_token")
                                logger.info(f"📦 登录响应keys: {list(login_data.keys())}")
                            
                            # 构建 cookies 字符串（包含所有必要的cookie字段）
                            cookies_parts = []
                            for key in ['UID', 'CID', 'SEID', 'KID']:
                                if key in cookie_dict:
                                    cookies_parts.append(f"{key}={cookie_dict[key]}")
                            
                            if cookies_parts and user_id:
                                cookies_str = '; '.join(cookies_parts)
                                logger.info(f"✅ 115登录成功: UID={user_id}, has_access_token={bool(access_token)}")
                                
                                # 直接从登录响应中构建用户信息（参考 p115_service.py.backup）
                                # 登录响应已包含所有必要信息
                                is_vip_value = login_data.get('is_vip', 0)
                                
                                # 解析 VIP 状态和等级
                                # is_vip: 0=普通用户, 大数字(如 4294967295)=VIP用户
                                # 实际VIP等级需要通过其他方式判断，这里简化处理
                                if isinstance(is_vip_value, int) and is_vip_value > 9:
                                    # 大数字表示VIP，但不知道具体等级，默认为VIP会员
                                    is_vip = True
                                    vip_level = 0  # 未知等级
                                    vip_name = 'VIP会员'
                                else:
                                    # 小数字直接表示等级
                                    is_vip = bool(is_vip_value and is_vip_value > 0)
                                    vip_level = is_vip_value
                                    vip_name = VIP_LEVEL_NAMES.get(is_vip_value, f'VIP{is_vip_value}' if is_vip else '普通用户')
                                
                                # 提取头像信息
                                face_info = login_data.get('face', {})
                                
                                user_info = {
                                    'user_id': user_id,
                                    'user_name': login_data.get('user_name', ''),
                                    'email': login_data.get('email', ''),
                                    'mobile': login_data.get('mobile', ''),
                                    'is_vip': is_vip,
                                    'vip_level': vip_level,
                                    'vip_name': vip_name,
                                    'face': {
                                        'face_l': face_info.get('face_l', ''),
                                        'face_m': face_info.get('face_m', ''),
                                        'face_s': face_info.get('face_s', '')
                                    },
                                    'country': login_data.get('country', ''),
                                    'space': {
                                        'total': 0,
                                        'used': 0,
                                        'remain': 0
                                    }
                                }
                                
                                logger.info(f"👤 用户信息: {user_info['user_name']} ({vip_name})")
                                
                                # 尝试获取空间信息（优先使用access_token）
                                try:
                                    temp_client = Pan115Client(
                                        app_id="",
                                        app_key="",
                                        user_id=user_id,
                                        user_key=cookies_str
                                    )
                                    
                                    # 🔑 如果有access_token,设置到client中
                                    if access_token:
                                        temp_client.access_token = access_token
                                        logger.info(f"🔑 使用access_token获取空间信息")
                                    
                                    # 只获取空间信息，不获取完整用户信息
                                    space_result = await temp_client._get_space_info_only()
                                    if space_result.get('success'):
                                        user_info['space'] = space_result.get('space', user_info['space'])
                                        logger.info(f"✅ 获取到空间信息: {space_result.get('space')}")
                                except Exception as e:
                                    logger.warning(f"⚠️ 获取空间信息失败，使用默认值: {e}")
                                
                                return {
                                    'success': True,
                                    'status': 'confirmed',
                                    'cookies': cookies_str,
                                    'user_id': user_id,
                                    'user_info': user_info,
                                    'access_token': access_token if access_token else None,  # 返回access_token
                                    'message': '登录成功'
                                }
                    
                    # 获取登录凭证失败
                    return {
                        'success': False,
                        'status': 'error',
                        'message': '获取登录凭证失败'
                    }
                    
                elif status_code == 1:
                    # 已扫码，等待确认
                    return {
                        'success': True,
                        'status': 'scanned',
                        'message': '已扫码，等待确认'
                    }
                elif status_code == -1 or status_code == -2:
                    # 已过期或取消
                    return {
                        'success': True,
                        'status': 'expired',
                        'message': '二维码已过期'
                    }
                else:
                    # 等待扫码
                    return {
                        'success': True,
                        'status': 'waiting',
                        'message': '等待扫码'
                    }
            else:
                return {
                    'success': False,
                    'status': 'error',
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 检查常规二维码状态异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'status': 'error',
                'message': str(e)
            }

