"""
115网盘 Open API 客户端
基于官方文档: https://www.yuque.com/115yun/open/fd7fidbgsritauxm
"""
import httpx
import hashlib
import time
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from log_manager import get_logger

logger = get_logger('pan115')


class Pan115Client:
    """115网盘 Open API 客户端（同时支持常规登录）"""
    
    def __init__(self, app_id: str, app_key: str, user_id: str, user_key: str):
        """
        初始化115网盘客户端
        
        Args:
            app_id: 应用ID
            app_key: 应用密钥
            user_id: 用户ID
            user_key: 用户密钥（从115 Open获取）
        """
        self.app_id = app_id
        self.app_key = app_key
        self.user_id = user_id
        self.user_key = user_key
        self.base_url = "https://proapi.115.com"
        self.auth_url = "https://passportapi.115.com"  # 认证API使用不同的域名
        self.webapi_url = "https://webapi.115.com"  # 常规 Web API
        
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
            async with httpx.AsyncClient(timeout=30.0) as client:
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
        
        Args:
            file_path: 本地文件路径
            target_dir_id: 目标目录ID，0表示根目录
            target_path: 目标路径（如果提供，会先创建目录）
            
        Returns:
            {"success": bool, "message": str, "file_id": str}
        """
        try:
            # 如果提供了路径，先创建目录
            if target_path and target_path != '/':
                dir_result = await self.create_directory_path(target_path)
                if dir_result['success']:
                    target_dir_id = dir_result['dir_id']
                else:
                    logger.warning(f"⚠️ 创建目录失败: {dir_result['message']}")
            
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
                
                async with httpx.AsyncClient(timeout=600.0) as client:
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
    
    async def create_directory_path(self, path: str, parent_id: str = "0") -> Dict[str, Any]:
        """
        创建目录路径（递归创建）
        
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
                
                # 创建目录
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
        
        Args:
            dir_name: 目录名称
            parent_id: 父目录ID，0表示根目录
            
        Returns:
            {"success": bool, "dir_id": str}
        """
        try:
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'cname': dir_name,
                'pid': parent_id,
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
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
                    # 目录已存在，尝试获取目录ID
                    logger.info(f"📁 目录已存在: {dir_name}")
                    # TODO: 查询目录获取ID
                    return {
                        'success': True,
                        'dir_id': parent_id  # 暂时返回父目录ID
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
            
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
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
            
            async with httpx.AsyncClient(timeout=10.0) as client:
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
            
            async with httpx.AsyncClient(timeout=10.0) as client:
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
                    user_info = {
                        'user_id': data.get('user_id', self.user_id),
                        'user_name': data.get('user_name', ''),
                        'email': data.get('email', ''),
                        'is_vip': bool(data.get('vip', {}).get('is_vip', 0)),
                        'vip_level': data.get('vip', {}).get('level', 0),
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
        
        由于115 Web API可能需要特殊认证，这里使用更通用的方法：
        通过已有的登录信息构建基本的用户信息
        
        Returns:
            与 get_user_info 相同的格式
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Cookie': self.user_key,  # user_key 存储的是 cookies
                'Accept': 'application/json, text/plain, */*',
            }
            
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                # 尝试获取文件列表来验证cookies有效性，同时获取空间信息
                # 115文件列表API: https://webapi.115.com/files
                list_response = await client.get(
                    f"{self.webapi_url}/files",
                    params={'aid': 1, 'cid': 0, 'o': 'user_ptime', 'asc': 0, 'offset': 0, 'show_dir': 1, 'limit': 1},
                    headers=headers
                )
            
            logger.info(f"📦 文件列表响应状态: {list_response.status_code}")
            
            if list_response.status_code == 200:
                list_result = list_response.json()
                logger.info(f"📦 文件列表数据（前200字符）: {str(list_result)[:200]}")
                
                # 检查响应状态
                if list_result.get('state') == False:
                    logger.warning(f"⚠️ API返回失败: {list_result.get('error', '未知错误')}")
                    # Cookies过期，返回基本信息并提示用户
                    # 注意：即使cookies过期，我们仍返回success=True，因为user_id是有效的
                    return {
                        'success': True,
                        'user_info': {
                            'user_id': self.user_id,
                            'user_name': f'用户 {self.user_id}',  # 使用UID作为显示名
                            'email': '',
                            'is_vip': False,
                            'vip_level': 0,
                            'space': {'total': 0, 'used': 0, 'remain': 0}
                        },
                        'message': '无法获取详细信息，Cookies可能已过期。空间信息将在重新登录后显示。'
                    }
                
                # 解析空间信息
                data = list_result.get('data', list_result)  # 有时数据直接在根级别
                space = data.get('space', {})
                count = data.get('count', {})
                
                user_info = {
                    'user_id': self.user_id,
                    'user_name': '',  # 文件列表API不包含用户名
                    'email': '',
                    'is_vip': False,  # 需要通过其他方式获取
                    'vip_level': 0,
                    'space': {
                        'total': int(space.get('all_total', {}).get('size', 0) if isinstance(space.get('all_total'), dict) else space.get('all_total', 0)),
                        'used': int(space.get('all_use', {}).get('size', 0) if isinstance(space.get('all_use'), dict) else space.get('all_use', 0)),
                        'remain': int(space.get('all_remain', {}).get('size', 0) if isinstance(space.get('all_remain'), dict) else space.get('all_remain', 0)),
                    }
                }
                
                logger.info(f"✅ 成功获取空间信息: 总={user_info['space']['total']}, 已用={user_info['space']['used']}")
                
                return {
                    'success': True,
                    'user_info': user_info,
                    'message': '获取用户信息成功'
                }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {list_response.status_code}"
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
        
        Returns:
            {
                "success": bool,
                "space": {"total": int, "used": int, "remain": int},
                "message": str
            }
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.user_key,
            }
            
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                # 使用文件列表API获取空间信息
                response = await client.get(
                    f"{self.webapi_url}/files",
                    params={'aid': 1, 'cid': 0, 'limit': 1},
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('state') == False:
                    # API调用失败，返回默认值
                    return {
                        'success': False,
                        'space': {'total': 0, 'used': 0, 'remain': 0},
                        'message': result.get('error', '获取失败')
                    }
                
                # 解析空间信息
                data = result.get('data', result)
                space = data.get('space', {})
                
                return {
                    'success': True,
                    'space': {
                        'total': int(space.get('all_total', {}).get('size', 0) if isinstance(space.get('all_total'), dict) else space.get('all_total', 0)),
                        'used': int(space.get('all_use', {}).get('size', 0) if isinstance(space.get('all_use'), dict) else space.get('all_use', 0)),
                        'remain': int(space.get('all_remain', {}).get('size', 0) if isinstance(space.get('all_remain'), dict) else space.get('all_remain', 0)),
                    },
                    'message': '获取空间信息成功'
                }
            else:
                return {
                    'success': False,
                    'space': {'total': 0, 'used': 0, 'remain': 0},
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ 获取空间信息异常: {e}")
            return {
                'success': False,
                'space': {'total': 0, 'used': 0, 'remain': 0},
                'message': str(e)
            }
    
    async def list_files(self, parent_id: str = "0", limit: int = 1150, 
                        offset: int = 0, show_dir: int = 1) -> Dict[str, Any]:
        """
        列出目录下的文件和文件夹
        
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
            
            async with httpx.AsyncClient(timeout=30.0) as client:
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
    
    async def delete_files(self, file_ids: List[str]) -> Dict[str, Any]:
        """
        删除文件或文件夹
        
        Args:
            file_ids: 文件ID列表（支持批量删除）
            
        Returns:
            {"success": bool, "message": str}
        """
        try:
            # 115 Open API 删除接口支持批量删除
            fid_str = ','.join(file_ids)
            
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'fid': fid_str,
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
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
    
    async def move_files(self, file_ids: List[str], target_dir_id: str) -> Dict[str, Any]:
        """
        移动文件或文件夹
        
        Args:
            file_ids: 要移动的文件ID列表
            target_dir_id: 目标目录ID
            
        Returns:
            {"success": bool, "message": str}
        """
        try:
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
            
            async with httpx.AsyncClient(timeout=30.0) as client:
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
    
    async def copy_files(self, file_ids: List[str], target_dir_id: str) -> Dict[str, Any]:
        """
        复制文件或文件夹
        
        Args:
            file_ids: 要复制的文件ID列表
            target_dir_id: 目标目录ID
            
        Returns:
            {"success": bool, "message": str}
        """
        try:
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
            
            async with httpx.AsyncClient(timeout=30.0) as client:
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
    
    async def rename_file(self, file_id: str, new_name: str) -> Dict[str, Any]:
        """
        重命名文件或文件夹
        
        Args:
            file_id: 文件或文件夹ID
            new_name: 新名称
            
        Returns:
            {"success": bool, "message": str}
        """
        try:
            params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'fid': file_id,
                'file_name': new_name,
            }
            
            params['sign'] = self._generate_signature(params)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
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
            
            async with httpx.AsyncClient(timeout=10.0) as client:
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
            
            async with httpx.AsyncClient(timeout=30.0) as client:
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
            
            async with httpx.AsyncClient(timeout=10.0) as client:
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
            
            async with httpx.AsyncClient(timeout=60.0) as client:
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
            
            async with httpx.AsyncClient(timeout=10.0) as client:
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
    
    @staticmethod
    async def get_regular_qrcode(app: str = "web") -> Dict[str, Any]:
        """
        获取常规115登录二维码（非 Open API）
        
        Args:
            app: 应用类型，可选值：
                - "web": 网页版（默认）
                - "android": Android客户端
                - "ios": iOS客户端
                - "tv": TV版
                - "alipaymini": 支付宝小程序
                - "wechatmini": 微信小程序
                - "qandroid": 115生活Android版
                
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
                "message": str
            }
        """
        try:
            # 115 常规登录二维码 API
            # 参考：https://github.com/ChenyangGao/web-mount-packs/tree/main/python-115-client
            url = "https://qrcodeapi.115.com/api/1.0/web/1.0/token"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
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
    
    @staticmethod
    async def check_regular_qrcode_status(qrcode_token: Dict[str, Any], app: str = "web") -> Dict[str, Any]:
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
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(status_url, params=params, headers=headers)
            
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
                    login_url = "https://passportapi.115.com/app/1.0/web/1.0/login/qrcode"
                    
                    login_params = {
                        'account': uid,
                        'app': app,
                    }
                    
                    async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as login_client:
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
                            
                            # 构建 cookies 字符串（包含所有必要的cookie字段）
                            cookies_parts = []
                            for key in ['UID', 'CID', 'SEID', 'KID']:
                                if key in cookie_dict:
                                    cookies_parts.append(f"{key}={cookie_dict[key]}")
                            
                            if cookies_parts and user_id:
                                cookies_str = '; '.join(cookies_parts)
                                logger.info(f"✅ 115登录成功: UID={user_id}")
                                
                                # 直接从登录响应中构建用户信息（不再调用额外API）
                                # 登录响应已包含所有必要信息
                                is_vip_value = login_data.get('is_vip', 0)
                                # is_vip 是一个大数字（如 4294967295）表示VIP，0表示非VIP
                                is_vip = bool(is_vip_value and is_vip_value > 0)
                                
                                user_info = {
                                    'user_id': user_id,
                                    'user_name': login_data.get('user_name', ''),
                                    'email': login_data.get('email', ''),
                                    'mobile': login_data.get('mobile', ''),
                                    'is_vip': is_vip,
                                    'vip_level': 0,  # 登录响应不包含具体等级
                                    'space': {
                                        'total': 0,
                                        'used': 0,
                                        'remain': 0
                                    }
                                }
                                
                                # 尝试获取空间信息（使用新保存的cookies）
                                try:
                                    temp_client = Pan115Client(
                                        app_id="",
                                        app_key="",
                                        user_id=user_id,
                                        user_key=cookies_str
                                    )
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

