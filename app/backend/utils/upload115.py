"""
115网盘上传核心逻辑
基于 fake115uploader 的完整实现
"""
import os
import time
import json
import asyncio
import base64
from typing import Dict, Any, Optional, Tuple, Callable
from pathlib import Path

import httpx
from log_manager import get_logger

# 尝试相对导入，如果失败则使用绝对导入
try:
    from .ecdh_cipher import create_ecdh_cipher, EcdhCipher
    from .file_hash import calculate_sha1, calculate_range_sha1
    from .upload_signature import create_signature_calculator, UploadSignature
except ImportError:
    from ecdh_cipher import create_ecdh_cipher, EcdhCipher
    from file_hash import calculate_sha1, calculate_range_sha1
    from upload_signature import create_signature_calculator, UploadSignature

logger = get_logger('upload115')


class Upload115:
    """115网盘上传器"""
    
    # API端点
    INIT_UPLOAD_URL = "https://uplb.115.com/4.0/initupload.php"
    GET_UPLOAD_INFO_URL = "https://uplb.115.com/3.0/getuploadinfo.php"
    LIST_FILE_URL = "https://webapi.115.com/files"
    
    # User Agent
    USER_AGENT = "Mozilla/5.0 115disk/30.5.1"
    ALI_USER_AGENT = "aliyun-sdk-android/2.9.1"
    
    def __init__(self, user_id: str, user_key: str, cookies: str, use_proxy: bool = False):
        """
        初始化上传器
        
        Args:
            user_id: 用户ID
            user_key: 用户密钥
            cookies: 用户Cookie
            use_proxy: 是否使用代理
        """
        self.user_id = user_id
        self.user_key = user_key
        self.cookies = cookies
        self.use_proxy = use_proxy
        
        # 创建加密器和签名计算器
        self.ecdh_cipher: Optional[EcdhCipher] = None
        self.signature: Optional[UploadSignature] = None
        
        # 初始化
        self._initialize()
    
    def _initialize(self):
        """初始化加密和签名组件"""
        self.ecdh_cipher = create_ecdh_cipher()
        self.signature = create_signature_calculator(self.user_id, self.user_key)
    
    def _get_client_kwargs(self, timeout: float = 30.0) -> Dict[str, Any]:
        """获取httpx客户端配置"""
        kwargs = {'timeout': timeout}
        
        if self.use_proxy:
            kwargs['trust_env'] = True
        else:
            kwargs['trust_env'] = False
            kwargs['proxies'] = None
        
        return kwargs
    
    async def upload_file(self, file_path: str, target_cid: str = "0",
                         progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        上传文件到115网盘
        
        Args:
            file_path: 本地文件路径
            target_cid: 目标目录ID（默认根目录）
            progress_callback: 进度回调函数
            
        Returns:
            上传结果字典
        """
        try:
            # 检查文件
            if not os.path.exists(file_path):
                return {'success': False, 'message': '文件不存在'}
            
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            logger.info(f"📤 开始上传: {filename} ({file_size} bytes)")
            
            # 计算文件SHA1
            logger.info("🔐 计算文件SHA1...")
            block_hash, total_hash = calculate_sha1(file_path)
            logger.info(f"📝 Block SHA1: {block_hash}")
            logger.info(f"📝 Total SHA1: {total_hash}")
            
            # 尝试秒传
            logger.info("⚡ 尝试秒传...")
            fast_result = await self._fast_upload(
                filename, file_size, total_hash, target_cid
            )
            
            # 检查秒传结果
            if fast_result['status'] == 'success':
                logger.info("✅ 秒传成功！")
                return {
                    'success': True,
                    'message': '秒传成功',
                    'quick_upload': True,
                    'file_id': fast_result.get('file_id', '')
                }
            
            elif fast_result['status'] == 'need_upload':
                # 需要实际上传
                logger.info("📤 秒传失败，开始上传到OSS...")
                fast_token = fast_result['fast_token']
                
                # 根据文件大小选择上传方式
                if file_size > 100 * 1024 * 1024:  # 大于100MB使用分片上传
                    logger.info("📦 使用分片上传模式")
                    upload_result = await self._multipart_upload(
                        file_path, fast_token, progress_callback
                    )
                else:
                    logger.info("📄 使用普通上传模式")
                    upload_result = await self._normal_upload(
                        file_path, fast_token, progress_callback
                    )
                
                return upload_result
            
            elif fast_result['status'] == 'need_verify':
                # 需要二次验证
                logger.info("🔐 需要二次验证...")
                sign_key = fast_result['sign_key']
                sign_check = fast_result['sign_check']
                
                # 计算指定范围的SHA1
                start, end = map(int, sign_check.split('-'))
                sign_val = calculate_range_sha1(file_path, start, end)
                logger.info(f"📝 验证范围 {sign_check}: {sign_val}")
                
                # 重新上传SHA1
                fast_result = await self._fast_upload(
                    filename, file_size, total_hash, target_cid,
                    sign_key=sign_key, sign_val=sign_val
                )
                
                # 递归处理结果
                if fast_result['status'] == 'success':
                    logger.info("✅ 二次验证后秒传成功！")
                    return {
                        'success': True,
                        'message': '秒传成功（二次验证）',
                        'quick_upload': True,
                        'file_id': fast_result.get('file_id', '')
                    }
                elif fast_result['status'] == 'need_upload':
                    # 继续上传流程
                    fast_token = fast_result['fast_token']
                    if file_size > 100 * 1024 * 1024:
                        upload_result = await self._multipart_upload(
                            file_path, fast_token, progress_callback
                        )
                    else:
                        upload_result = await self._normal_upload(
                            file_path, fast_token, progress_callback
                        )
                    return upload_result
                else:
                    return {'success': False, 'message': fast_result.get('message', '上传失败')}
            
            else:
                # 其他错误
                return {'success': False, 'message': fast_result.get('message', '上传失败')}
        
        except Exception as e:
            logger.error(f"❌ 上传异常: {e}", exc_info=True)
            return {'success': False, 'message': str(e)}
    
    async def _fast_upload(self, filename: str, file_size: int, 
                          file_sha1: str, target_cid: str,
                          sign_key: str = "", sign_val: str = "") -> Dict[str, Any]:
        """
        尝试秒传（上传SHA1到115服务器）
        
        Args:
            filename: 文件名
            file_size: 文件大小
            file_sha1: 文件SHA1（大写）
            target_cid: 目标目录ID
            sign_key: 二次验证key
            sign_val: 二次验证value
            
        Returns:
            结果字典，包含status: 'success'|'need_upload'|'need_verify'|'error'
        """
        try:
            timestamp = int(time.time())
            
            # 构建表单数据
            form_data = self.signature.build_upload_form(
                filename, file_size, file_sha1, target_cid,
                sign_key, sign_val, timestamp
            )
            
            logger.debug(f"表单数据: {form_data}")
            
            # ECDH加密表单
            encrypted_data = self.ecdh_cipher.encrypt(form_data.encode())
            
            # 生成k_ec参数
            k_ec = self.ecdh_cipher.encode_token(timestamp)
            
            # 发送请求
            url = f"{self.INIT_UPLOAD_URL}?k_ec={k_ec}"
            headers = {
                'User-Agent': self.USER_AGENT,
                'Cookie': self.cookies,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs()) as client:
                response = await client.post(url, content=encrypted_data, headers=headers)
            
            logger.debug(f"秒传响应: HTTP {response.status_code}")
            
            if response.status_code != 200:
                return {
                    'status': 'error',
                    'message': f'请求失败: HTTP {response.status_code}'
                }
            
            # ECDH解密响应
            decrypted_data = self.ecdh_cipher.decrypt(response.content)
            result = json.loads(decrypted_data)
            
            logger.debug(f"秒传结果: {result}")
            
            # 解析响应
            status = result.get('status')
            statuscode = result.get('statuscode')
            
            if status == 2 and statuscode == 0:
                # 秒传成功
                return {
                    'status': 'success',
                    'file_id': result.get('fileid', ''),
                    'pick_code': result.get('pickcode', '')
                }
            
            elif status == 7 and statuscode == 701:
                # 需要二次验证
                return {
                    'status': 'need_verify',
                    'sign_key': result.get('sign_key', ''),
                    'sign_check': result.get('sign_check', '')
                }
            
            elif status == 1 and statuscode == 0:
                # 秒传失败，需要实际上传
                return {
                    'status': 'need_upload',
                    'fast_token': result  # 包含bucket, object, callback等信息
                }
            
            else:
                # 其他错误
                return {
                    'status': 'error',
                    'message': f"未知状态: status={status}, statuscode={statuscode}"
                }
        
        except Exception as e:
            logger.error(f"❌ 秒传异常: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    async def _get_oss_token(self) -> Dict[str, Any]:
        """
        获取OSS上传凭证
        
        Returns:
            OSS凭证字典
        """
        try:
            headers = {
                'User-Agent': self.USER_AGENT,
                'Cookie': self.cookies,
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs()) as client:
                response = await client.get(self.GET_UPLOAD_INFO_URL, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"获取OSS凭证失败: HTTP {response.status_code}")
            
            result = response.json()
            logger.debug(f"OSS凭证: {result}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 获取OSS凭证异常: {e}", exc_info=True)
            raise
    
    async def _normal_upload(self, file_path: str, fast_token: Dict[str, Any],
                           progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        普通OSS上传（适用于小文件）
        
        Args:
            file_path: 文件路径
            fast_token: 秒传返回的token信息
            progress_callback: 进度回调
            
        Returns:
            上传结果
        """
        try:
            # 获取OSS凭证
            oss_info = await self._get_oss_token()
            
            endpoint = oss_info.get('endpoint', '')
            access_key_id = oss_info.get('AccessKeyId', '')
            access_key_secret = oss_info.get('AccessKeySecret', '')
            security_token = oss_info.get('SecurityToken', '')
            
            if not all([endpoint, access_key_id, access_key_secret]):
                raise Exception("OSS凭证不完整")
            
            # 从fast_token获取bucket和object
            bucket = fast_token.get('bucket', '')
            object_key = fast_token.get('object', '')
            callback_info = fast_token.get('callback', {})
            
            logger.info(f"📤 Bucket: {bucket}")
            logger.info(f"📤 Object: {object_key}")
            
            # 使用阿里云OSS SDK上传
            try:
                import oss2
                
                # 创建OSS客户端
                auth = oss2.StsAuth(access_key_id, access_key_secret, security_token)
                bucket_obj = oss2.Bucket(auth, endpoint, bucket)
                
                # 准备回调
                callback_url = callback_info.get('callback', '')
                callback_var = callback_info.get('callback_var', '')
                
                callback_dict = {
                    'callbackUrl': base64.b64encode(callback_url.encode()).decode(),
                    'callbackBody': callback_var,
                    'callbackBodyType': 'application/x-www-form-urlencoded'
                }
                
                # 上传文件
                headers = {
                    'x-oss-security-token': security_token,
                    'User-Agent': self.ALI_USER_AGENT,
                }
                
                # 上传
                result = bucket_obj.put_object_from_file(
                    object_key, file_path,
                    headers=headers
                )
                
                logger.info(f"✅ OSS上传完成: {result.status}")
                
                # 验证上传
                is_verified = await self._verify_upload(fast_token.get('SHA1', ''))
                
                if is_verified:
                    return {
                        'success': True,
                        'message': '上传成功',
                        'quick_upload': False
                    }
                else:
                    return {
                        'success': False,
                        'message': '上传验证失败'
                    }
            
            except ImportError:
                logger.error("❌ 缺少oss2库，请安装: pip install oss2")
                return {
                    'success': False,
                    'message': '缺少oss2依赖库'
                }
        
        except Exception as e:
            logger.error(f"❌ 普通上传异常: {e}", exc_info=True)
            return {'success': False, 'message': str(e)}
    
    async def _multipart_upload(self, file_path: str, fast_token: Dict[str, Any],
                               progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        分片OSS上传（适用于大文件）
        
        Args:
            file_path: 文件路径
            fast_token: 秒传返回的token信息
            progress_callback: 进度回调
            
        Returns:
            上传结果
        """
        try:
            # 获取OSS凭证
            oss_info = await self._get_oss_token()
            
            endpoint = oss_info.get('endpoint', '')
            access_key_id = oss_info.get('AccessKeyId', '')
            access_key_secret = oss_info.get('AccessKeySecret', '')
            security_token = oss_info.get('SecurityToken', '')
            
            # 从fast_token获取信息
            bucket = fast_token.get('bucket', '')
            object_key = fast_token.get('object', '')
            file_sha1 = fast_token.get('SHA1', '')
            callback_info = fast_token.get('callback', {})
            
            file_size = os.path.getsize(file_path)
            
            logger.info(f"📦 开始分片上传: {file_size} bytes")
            
            try:
                import oss2
                
                # 创建OSS客户端
                auth = oss2.StsAuth(access_key_id, access_key_secret, security_token)
                bucket_obj = oss2.Bucket(auth, endpoint, bucket)
                
                # 计算分片数量
                part_size = oss2.determine_part_size(file_size, preferred_size=10 * 1024 * 1024)
                
                # 初始化分片上传
                upload_id = bucket_obj.init_multipart_upload(
                    object_key,
                    headers={
                        'x-oss-security-token': security_token,
                        'User-Agent': self.ALI_USER_AGENT,
                    }
                ).upload_id
                
                logger.info(f"📦 Upload ID: {upload_id}")
                
                # 上传分片
                parts = []
                with open(file_path, 'rb') as f:
                    part_number = 1
                    
                    while True:
                        data = f.read(part_size)
                        if not data:
                            break
                        
                        # 上传分片（带重试）
                        for retry in range(3):
                            try:
                                result = bucket_obj.upload_part(
                                    object_key, upload_id, part_number, data,
                                    headers={
                                        'x-oss-security-token': security_token,
                                        'User-Agent': self.ALI_USER_AGENT,
                                    }
                                )
                                parts.append(oss2.models.PartInfo(part_number, result.etag))
                                
                                logger.info(f"✅ 分片 {part_number} 上传成功")
                                
                                # 调用进度回调
                                if progress_callback:
                                    await progress_callback(part_number * part_size, file_size)
                                
                                break
                            except Exception as e:
                                logger.warning(f"⚠️  分片 {part_number} 上传失败 (重试 {retry+1}/3): {e}")
                                if retry == 2:
                                    raise
                                await asyncio.sleep(1)
                        
                        part_number += 1
                
                # 完成分片上传
                callback_url = callback_info.get('callback', '')
                callback_var = callback_info.get('callback_var', '')
                
                headers = {
                    'x-oss-security-token': security_token,
                    'x-oss-hash-sha1': file_sha1,  # 重要：SHA1验证
                    'User-Agent': self.ALI_USER_AGENT,
                }
                
                result = bucket_obj.complete_multipart_upload(
                    object_key, upload_id, parts,
                    headers=headers
                )
                
                logger.info(f"✅ 分片上传完成: {result.status}")
                
                # 验证上传
                is_verified = await self._verify_upload(file_sha1)
                
                if is_verified:
                    return {
                        'success': True,
                        'message': '分片上传成功',
                        'quick_upload': False
                    }
                else:
                    return {
                        'success': False,
                        'message': '上传验证失败'
                    }
            
            except ImportError:
                logger.error("❌ 缺少oss2库，请安装: pip install oss2")
                return {
                    'success': False,
                    'message': '缺少oss2依赖库'
                }
        
        except Exception as e:
            logger.error(f"❌ 分片上传异常: {e}", exc_info=True)
            return {'success': False, 'message': str(e)}
    
    async def _verify_upload(self, expected_sha1: str, target_cid: str = "0") -> bool:
        """
        验证文件是否上传成功
        
        通过查询目标目录的文件列表，检查最新文件的SHA1是否匹配
        
        Args:
            expected_sha1: 期望的SHA1值
            target_cid: 目标目录ID
            
        Returns:
            是否验证成功
        """
        try:
            url = f"{self.LIST_FILE_URL}?aid=1&cid={target_cid}&o=user_utime&asc=0&offset=0&show_dir=1&limit=20&code=&scid=&snap=0&natsort=1&source=&format=json&type=&star=&is_share=&suffix=&custom_order=0&fc_mix=0"
            
            headers = {
                'User-Agent': self.USER_AGENT,
                'Cookie': self.cookies,
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs()) as client:
                response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.warning(f"验证请求失败: HTTP {response.status_code}")
                return False
            
            result = response.json()
            files = result.get('data', [])
            
            if not files:
                logger.warning("目录为空，无法验证")
                return False
            
            # 检查第一个文件（最新文件）的SHA1
            latest_file = files[0]
            file_sha1 = latest_file.get('sha', '').upper()
            
            logger.info(f"验证SHA1: {file_sha1} vs {expected_sha1}")
            
            return file_sha1 == expected_sha1.upper()
        
        except Exception as e:
            logger.error(f"❌ 验证上传异常: {e}", exc_info=True)
            return False


def create_uploader(user_id: str, user_key: str, cookies: str, use_proxy: bool = False) -> Upload115:
    """创建上传器实例"""
    return Upload115(user_id, user_key, cookies, use_proxy)

