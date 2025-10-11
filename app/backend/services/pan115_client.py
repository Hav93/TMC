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
    """115网盘 Open API 客户端"""
    
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
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        try:
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
                if result.get('state') == True or result.get('code') == 0:
                    return {
                        'success': True,
                        'message': '115网盘连接成功',
                        'user_info': result.get('data', {})
                    }
                else:
                    return {
                        'success': False,
                        'message': f"认证失败: {result.get('message', '未知错误')}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"连接失败: HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"连接异常: {str(e)}"
            }

