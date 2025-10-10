"""
CloudDrive2 gRPC-Web 客户端
基于 gRPC-Web 协议与 CloudDrive2 通信
"""
import struct
import httpx
from typing import Optional, List, Dict, Any
from urllib.parse import unquote
from log_manager import get_logger

try:
    from services.clouddrive_pb2 import (
        GetTokenRequest,
        JWTToken,
        GetSubFilesRequest,
        SubFilesReply,
        AddOfflineFileRequest,
        FileOperationResult,
        UploadFileRequest,
        CopyFileRequest,
        MoveFileRequest,
        CreateFolderRequest,
        DeleteFileRequest
    )
except ImportError:
    # 如果导入失败，使用简化版本
    from clouddrive_pb2 import (
        GetTokenRequest,
        JWTToken,
        AddOfflineFileRequest,
        FileOperationResult,
        UploadFileRequest,
        CopyFileRequest,
        MoveFileRequest,
        CreateFolderRequest,
        DeleteFileRequest
    )

logger = get_logger('clouddrive2')


class CloudDrive2Client:
    """CloudDrive2 gRPC-Web 客户端"""
    
    def __init__(self, url: str, username: str, password: str):
        self.url = self._clean_url(url)
        self.username = username
        self.password = password
        self._token_cache = None
    
    def _clean_url(self, url: str) -> str:
        """清理URL格式"""
        if not url:
            return ""
        
        # 移除协议前缀
        if url.startswith('http://'):
            url = url[7:]
        elif url.startswith('https://'):
            url = url[8:]
        
        # 移除末尾斜杠
        url = url.rstrip('/')
        
        # 重新添加协议
        return f"http://{url}"
    
    def _build_grpc_payload(self, protobuf_bytes: bytes) -> bytes:
        """构建 gRPC-Web payload"""
        prefix = b'\x00' + struct.pack('>I', len(protobuf_bytes))
        return prefix + protobuf_bytes
    
    def _parse_grpc_response(self, raw_response: bytes) -> bytes:
        """解析 gRPC-Web 响应"""
        if len(raw_response) < 5:
            raise ValueError("响应太短，无法解析")
        
        length = int.from_bytes(raw_response[1:5], byteorder="big")
        return raw_response[5:5 + length]
    
    async def get_token(self) -> Optional[str]:
        """获取 JWT Token"""
        if self._token_cache:
            return self._token_cache
        
        try:
            # 创建 gRPC 请求
            request = GetTokenRequest(
                userName=self.username,
                password=self.password
            )
            protobuf_bytes = request.SerializeToString()
            payload = self._build_grpc_payload(protobuf_bytes)
            
            # gRPC-Web headers
            headers = {
                "Content-Type": "application/grpc-web",
                "Accept": "*/*",
                "X-User-Agent": "grpc-python/1.0",
                "X-Grpc-Web": "1",
            }
            
            endpoint = f"{self.url}/clouddrive.CloudDriveFileSrv/GetToken"
            logger.info(f"🔗 请求 CloudDrive Token: {endpoint}")
            logger.info(f"👤 用户名: {self.username}, 密码长度: {len(self.password)}")
            logger.info(f"📦 Protobuf 数据长度: {len(protobuf_bytes)} bytes")
            logger.info(f"📦 Payload 长度: {len(payload)} bytes")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    endpoint,
                    content=payload,
                    headers=headers
                )
            
            logger.info(f"📥 响应状态: {response.status_code}")
            logger.info(f"📥 响应长度: {len(response.content)} bytes")
            
            # 检查 gRPC 错误（通过 HTTP headers）
            if response.headers.get("grpc-message"):
                error_msg = unquote(response.headers.get("grpc-message"))
                grpc_status = response.headers.get("grpc-status", "unknown")
                logger.error(f"❌ gRPC 错误 (状态码: {grpc_status}): {error_msg}")
                return None
            
            if response.status_code != 200:
                logger.error(f"❌ GetToken 失败: HTTP {response.status_code}")
                return None
            
            if len(response.content) == 0:
                logger.error(f"❌ GetToken 响应为空")
                return None
            
            # 解析响应
            message_bytes = self._parse_grpc_response(response.content)
            logger.info(f"📥 解析后的消息长度: {len(message_bytes)} bytes")
            jwt_token = JWTToken()
            jwt_token.ParseFromString(message_bytes)
            
            if jwt_token.success:
                self._token_cache = jwt_token.token
                logger.info("✅ CloudDrive Token 获取成功")
                return jwt_token.token
            else:
                logger.error(f"❌ 获取 Token 失败: {jwt_token.errorMessage}")
                return None
        
        except Exception as e:
            logger.error(f"❌ 获取 CloudDrive Token 异常: {e}")
            return None
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        try:
            self._token_cache = None  # 清除缓存
            token = await self.get_token()
            
            if token:
                return {
                    "success": True,
                    "message": "CloudDrive 连接成功"
                }
            else:
                return {
                    "success": False,
                    "message": "CloudDrive 认证失败"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接失败: {str(e)}"
            }
    
    async def list_files(self, path: str = "/") -> Dict[str, Any]:
        """
        列出目录文件 (尝试多个可能的方法名)
        CloudDrive2 可能使用的方法名:
        - GetSubFiles
        - ListFiles  
        - GetFileList
        """
        token = await self.get_token()
        if not token:
            return {
                "success": False,
                "message": "无法获取认证 Token",
                "directories": []
            }
        
        # 尝试不同的方法名
        method_names = [
            "GetSubFiles",
            "ListFiles",
            "GetFileList",
            "QueryFileList"
        ]
        
        for method_name in method_names:
            try:
                logger.info(f"🔍 尝试方法: {method_name}")
                result = await self._try_list_method(method_name, path, token)
                if result["success"]:
                    logger.info(f"✅ 方法 {method_name} 成功")
                    return result
            except Exception as e:
                logger.warning(f"⚠️ 方法 {method_name} 失败: {e}")
                continue
        
        return {
            "success": False,
            "message": "所有列表方法都失败，CloudDrive 可能不支持目录浏览 API",
            "directories": []
        }
    
    async def _try_list_method(self, method_name: str, path: str, token: str) -> Dict[str, Any]:
        """尝试调用特定的列表方法"""
        # 简单的 protobuf 编码 (field 1 = path)
        path_bytes = path.encode('utf-8')
        protobuf_bytes = b'\x0a' + len(path_bytes).to_bytes(1, 'big') + path_bytes
        payload = self._build_grpc_payload(protobuf_bytes)
        
        headers = {
            "Content-Type": "application/grpc-web",
            "Accept": "*/*",
            "X-User-Agent": "grpc-python/1.0",
            "X-Grpc-Web": "1",
            "Authorization": f"Bearer {token}",
        }
        
        endpoint = f"{self.url}/clouddrive.CloudDriveFileSrv/{method_name}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                endpoint,
                content=payload,
                headers=headers
            )
        
        # 检查 gRPC 错误
        if response.headers.get("grpc-message"):
            error_msg = unquote(response.headers.get("grpc-message"))
            raise Exception(f"gRPC 错误: {error_msg}")
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        # 解析响应
        logger.info(f"📥 响应长度: {len(response.content)} bytes")
        
        if len(response.content) == 0:
            # 空响应，可能是该方法不支持或路径为空
            return {
                "success": True,
                "directories": [],
                "files": [],
                "current_path": path,
                "message": "目录为空或方法不支持"
            }
        
        # 使用真正的 protobuf 解析
        try:
            message_bytes = self._parse_grpc_response(response.content)
            logger.info(f"📦 解析后的消息长度: {len(message_bytes)} bytes")
            
            # 使用 SubFilesReply 正确解析
            from services.clouddrive_pb2 import SubFilesReply
            
            reply = SubFilesReply()
            reply.ParseFromString(message_bytes)
            
            # 转换为我们的格式
            directories = []
            files = []
            
            for item in reply.subFiles:
                # 智能判断：如果isFolder没有设置，通过路径和名称推断
                is_directory = item.isFolder
                
                # 如果isFolder为False但size为0且路径以名称结尾，很可能是目录（CloudDrive挂载点）
                if not is_directory and item.size == 0:
                    # 检查是否是根目录下的挂载点
                    if path in ['/', ''] and not item.name.endswith('.'):
                        # 根目录下的项目，如果路径包含名称，很可能是目录
                        if item.name in item.path:
                            is_directory = True
                
                if is_directory:
                    # 是目录
                    directories.append({
                        "name": item.name,
                        "path": item.path,
                        "isDirectory": True
                    })
                else:
                    # 是文件
                    files.append({
                        "name": item.name,
                        "path": item.path,
                        "size": item.size,
                        "isDirectory": False
                    })
            
            logger.info(f"✅ 成功解析: {len(directories)} 个目录, {len(files)} 个文件")
            
            return {
                "success": True,
                "directories": directories,
                "files": files,
                "current_path": path,
                "message": f"成功解析 {len(directories)} 个目录, {len(files)} 个文件"
            }
        except Exception as e:
            logger.warning(f"⚠️ protobuf 解析失败: {e}")
            # 解析失败，但至少说明有数据返回
            return {
                "success": True,
                "directories": [],
                "files": [],
                "current_path": path,
                "message": f"获取成功但解析失败 ({len(response.content)} bytes)"
            }
    
    async def push_magnet_with_folder(self, magnet_urls: List[str], target_path: str = "/") -> Dict[str, Any]:
        """
        推送磁力链接并自动创建目录（适用于 /115open 等需要先创建目录的路径）
        
        Args:
            magnet_urls: 磁力链接列表
            target_path: 目标路径
            
        Returns:
            {"success": bool, "message": str}
        """
        # 检查是否为需要先创建目录的路径
        needs_create = target_path.startswith("/115open")
        
        if needs_create:
            logger.info(f"📂 检测到 /115open 路径，先创建目录: {target_path}")
            create_result = await self.create_folder(target_path)
            
            if not create_result["success"]:
                # 如果创建失败但不是"已存在"错误，记录警告
                if "already exists" not in create_result.get("message", "").lower():
                    logger.warning(f"⚠️ 创建目录失败: {create_result.get('message')}")
        
        # 推送磁力链接
        return await self.push_magnet(magnet_urls, target_path)
    
    async def push_magnet(self, magnet_urls: List[str], target_path: str = "/") -> Dict[str, Any]:
        """推送磁力链接到 CloudDrive"""
        token = await self.get_token()
        if not token:
            return {"success": False, "message": "无法获取认证 Token"}
        
        try:
            # 创建请求
            urls_str = '\n'.join(magnet_urls)
            request = AddOfflineFileRequest(
                urls=urls_str,
                toFolder=target_path
            )
            protobuf_bytes = request.SerializeToString()
            payload = self._build_grpc_payload(protobuf_bytes)
            
            headers = {
                "Content-Type": "application/grpc-web",
                "Accept": "*/*",
                "X-User-Agent": "grpc-python/1.0",
                "X-Grpc-Web": "1",
                "Authorization": f"Bearer {token}",
            }
            
            endpoint = f"{self.url}/clouddrive.CloudDriveFileSrv/AddOfflineFiles"
            logger.info(f"📤 推送 {len(magnet_urls)} 个磁力链接到: {target_path}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    endpoint,
                    content=payload,
                    headers=headers
                )
            
            # 检查 gRPC 错误
            if response.headers.get("grpc-message"):
                error_msg = unquote(response.headers.get("grpc-message"))
                return {"success": False, "message": f"CloudDrive 错误: {error_msg}"}
            
            if response.status_code != 200:
                return {"success": False, "message": f"HTTP {response.status_code}"}
            
            # 解析响应
            message_bytes = self._parse_grpc_response(response.content)
            result = FileOperationResult()
            result.ParseFromString(message_bytes)
            
            if result.success:
                logger.info("✅ 磁力链接推送成功")
                return {
                    "success": True,
                    "message": f"成功推送 {len(magnet_urls)} 个磁力链接"
                }
            else:
                logger.error(f"❌ 推送失败: {result.errorMessage}")
                return {"success": False, "message": result.errorMessage}
        
        except Exception as e:
            logger.error(f"❌ 推送磁力链接异常: {e}")
            return {"success": False, "message": str(e)}
    
    async def upload_file(self, local_file_path: str, remote_path: str = "/", 
                         file_name: Optional[str] = None) -> Dict[str, Any]:
        """
        上传本地文件到 CloudDrive（使用 HTTP multipart/form-data）
        
        这个方法使用 CloudDrive2 Web 端的上传 API，
        通过 HTTP multipart/form-data 上传文件，无需挂载路径。
        
        Args:
            local_file_path: 本地文件完整路径
            remote_path: CloudDrive 远程目录路径（如 /115open/Media/Movies）
            file_name: 可选的新文件名，默认使用原文件名
            
        Returns:
            {"success": bool, "message": str}
        """
        token = await self.get_token()
        if not token:
            return {"success": False, "message": "无法获取认证 Token"}
        
        try:
            import os
            if not os.path.exists(local_file_path):
                return {"success": False, "message": f"本地文件不存在: {local_file_path}"}
            
            if not file_name:
                file_name = os.path.basename(local_file_path)
            
            file_size = os.path.getsize(local_file_path)
            logger.info(f"📤 开始上传文件: {file_name} ({file_size} bytes) → {remote_path}")
            
            # 尝试 HTTP multipart/form-data 上传
            try:
                result = await self._upload_via_http(local_file_path, remote_path, file_name, token)
                if result["success"]:
                    return result
            except Exception as e:
                logger.warning(f"⚠️ HTTP 上传失败: {e}，尝试 gRPC 方法")
            
            # 如果 HTTP 失败，尝试 gRPC 方法
            upload_methods = [
                "UploadFile",
                "UploadLocalFile", 
                "PutFile",
                "UploadFromLocal"
            ]
            
            for method_name in upload_methods:
                try:
                    logger.info(f"🔍 尝试 gRPC 上传方法: {method_name}")
                    result = await self._try_upload_method(
                        method_name, local_file_path, remote_path, file_name, token
                    )
                    if result["success"]:
                        logger.info(f"✅ 上传成功: {file_name} -> {remote_path}")
                        return result
                except Exception as e:
                    logger.warning(f"⚠️ 方法 {method_name} 失败: {e}")
                    continue
            
            return {
                "success": False,
                "message": "所有上传方法都失败，CloudDrive 可能不支持此 API"
            }
        
        except Exception as e:
            logger.error(f"❌ 上传文件异常: {e}")
            return {"success": False, "message": str(e)}
    
    async def _upload_via_http(self, local_file_path: str, remote_path: str, 
                               file_name: str, token: str) -> Dict[str, Any]:
        """
        使用 HTTP multipart/form-data 上传文件（CloudDrive2 Web 端方式）
        
        这是 CloudDrive2 Web 界面使用的上传方式，
        通过 HTTP POST 上传文件，无需文件在挂载路径下。
        """
        import os
        
        # 尝试不同的 API 端点
        api_endpoints = [
            "/api/upload",  # 标准上传端点
            "/api/v1/upload",  # v1 版本
            "/api/fs/upload",  # 文件系统上传
            "/upload",  # 简单端点
        ]
        
        for endpoint in api_endpoints:
            try:
                upload_url = f"{self.url}{endpoint}"
                logger.info(f"🔗 尝试 HTTP 上传端点: {upload_url}")
                
                # 准备 multipart/form-data
                with open(local_file_path, 'rb') as f:
                    files = {
                        'file': (file_name, f, 'application/octet-stream')
                    }
                    
                    data = {
                        'path': remote_path,
                        'name': file_name,
                    }
                    
                    headers = {
                        "Authorization": f"Bearer {token}",
                    }
                    
                    async with httpx.AsyncClient(timeout=300.0) as client:  # 5分钟超时
                        response = await client.post(
                            upload_url,
                            files=files,
                            data=data,
                            headers=headers
                        )
                    
                    logger.info(f"📥 HTTP 响应状态: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            if result.get("success") or result.get("code") == 0:
                                logger.info(f"✅ HTTP 上传成功: {file_name}")
                                return {"success": True, "message": "文件上传成功"}
                            else:
                                error_msg = result.get("message", "未知错误")
                                logger.warning(f"⚠️ 上传失败: {error_msg}")
                        except:
                            # 如果无法解析 JSON，但状态码是 200，认为成功
                            logger.info(f"✅ HTTP 上传成功（无 JSON 响应）")
                            return {"success": True, "message": "文件上传成功"}
                    elif response.status_code == 404:
                        logger.debug(f"⚠️ 端点不存在: {endpoint}")
                        continue
                    else:
                        logger.warning(f"⚠️ HTTP {response.status_code}: {response.text[:200]}")
                        
            except Exception as e:
                logger.debug(f"⚠️ 端点 {endpoint} 失败: {e}")
                continue
        
        raise Exception("所有 HTTP 上传端点都失败")
    
    async def _try_upload_method(self, method_name: str, local_path: str, 
                                 remote_path: str, file_name: str, token: str) -> Dict[str, Any]:
        """尝试使用特定方法上传文件"""
        request = UploadFileRequest(
            localPath=local_path,
            remotePath=remote_path,
            fileName=file_name
        )
        protobuf_bytes = request.SerializeToString()
        payload = self._build_grpc_payload(protobuf_bytes)
        
        headers = {
            "Content-Type": "application/grpc-web",
            "Accept": "*/*",
            "X-User-Agent": "grpc-python/1.0",
            "X-Grpc-Web": "1",
            "Authorization": f"Bearer {token}",
        }
        
        endpoint = f"{self.url}/clouddrive.CloudDriveFileSrv/{method_name}"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                content=payload,
                headers=headers
            )
        
        if response.headers.get("grpc-message"):
            error_msg = unquote(response.headers.get("grpc-message"))
            raise Exception(f"gRPC 错误: {error_msg}")
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        message_bytes = self._parse_grpc_response(response.content)
        result = FileOperationResult()
        result.ParseFromString(message_bytes)
        
        if result.success:
            return {
                "success": True,
                "message": f"文件上传成功: {file_name}"
            }
        else:
            return {"success": False, "message": result.errorMessage}
    
    async def copy_file(self, source_path: str, target_path: str) -> Dict[str, Any]:
        """
        在 CloudDrive 内复制文件
        
        Args:
            source_path: 源文件路径
            target_path: 目标文件路径（包含文件名）
        """
        token = await self.get_token()
        if not token:
            return {"success": False, "message": "无法获取认证 Token"}
        
        try:
            copy_methods = ["CopyFile", "CopyFiles", "FileCopy"]
            
            for method_name in copy_methods:
                try:
                    logger.info(f"🔍 尝试复制方法: {method_name}")
                    result = await self._try_file_operation(
                        method_name, source_path, target_path, token
                    )
                    if result["success"]:
                        logger.info(f"✅ 复制成功: {source_path} -> {target_path}")
                        return result
                except Exception as e:
                    logger.warning(f"⚠️ 方法 {method_name} 失败: {e}")
                    continue
            
            return {
                "success": False,
                "message": "所有复制方法都失败"
            }
        
        except Exception as e:
            logger.error(f"❌ 复制文件异常: {e}")
            return {"success": False, "message": str(e)}
    
    async def move_file(self, source_path: str, target_path: str) -> Dict[str, Any]:
        """
        在 CloudDrive 内移动文件
        
        Args:
            source_path: 源文件路径
            target_path: 目标文件路径（包含文件名）
        """
        token = await self.get_token()
        if not token:
            return {"success": False, "message": "无法获取认证 Token"}
        
        try:
            move_methods = ["MoveFile", "MoveFiles", "FileMove", "RenameFile"]
            
            for method_name in move_methods:
                try:
                    logger.info(f"🔍 尝试移动方法: {method_name}")
                    result = await self._try_file_operation(
                        method_name, source_path, target_path, token, is_move=True
                    )
                    if result["success"]:
                        logger.info(f"✅ 移动成功: {source_path} -> {target_path}")
                        return result
                except Exception as e:
                    logger.warning(f"⚠️ 方法 {method_name} 失败: {e}")
                    continue
            
            return {
                "success": False,
                "message": "所有移动方法都失败"
            }
        
        except Exception as e:
            logger.error(f"❌ 移动文件异常: {e}")
            return {"success": False, "message": str(e)}
    
    async def _try_file_operation(self, method_name: str, source_path: str, 
                                  target_path: str, token: str, is_move: bool = False) -> Dict[str, Any]:
        """通用的文件操作方法（复制/移动）"""
        if is_move:
            request = MoveFileRequest(sourcePath=source_path, targetPath=target_path)
        else:
            request = CopyFileRequest(sourcePath=source_path, targetPath=target_path)
        
        protobuf_bytes = request.SerializeToString()
        payload = self._build_grpc_payload(protobuf_bytes)
        
        headers = {
            "Content-Type": "application/grpc-web",
            "Accept": "*/*",
            "X-User-Agent": "grpc-python/1.0",
            "X-Grpc-Web": "1",
            "Authorization": f"Bearer {token}",
        }
        
        endpoint = f"{self.url}/clouddrive.CloudDriveFileSrv/{method_name}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint,
                content=payload,
                headers=headers
            )
        
        if response.headers.get("grpc-message"):
            error_msg = unquote(response.headers.get("grpc-message"))
            raise Exception(f"gRPC 错误: {error_msg}")
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        message_bytes = self._parse_grpc_response(response.content)
        result = FileOperationResult()
        result.ParseFromString(message_bytes)
        
        if result.success:
            return {"success": True, "message": "操作成功"}
        else:
            return {"success": False, "message": result.errorMessage}
    
    async def create_folder(self, path: str) -> Dict[str, Any]:
        """
        创建文件夹（仅支持本地存储路径，如 /downloads）
        
        注意：
        - CloudDrive 的云存储路径不支持手动创建文件夹
        - 仅本地文件系统路径（如 /downloads）支持此操作
        - 对于云存储，建议使用 push_magnet 推送离线下载任务，CloudDrive 会自动创建目录
        
        Args:
            path: 完整文件夹路径，如 "/downloads/Movies/2024"
            
        Returns:
            {"success": bool, "message": str}
        """
        token = await self.get_token()
        if not token:
            return {"success": False, "message": "无法获取认证 Token"}
        
        try:
            # 使用完整路径创建文件夹
            path_bytes = path.encode('utf-8')
            protobuf_bytes = b'\x0a' + bytes([len(path_bytes)]) + path_bytes
            payload = self._build_grpc_payload(protobuf_bytes)
            
            headers = {
                "Content-Type": "application/grpc-web",
                "Accept": "*/*",
                "X-User-Agent": "grpc-python/1.0",
                "X-Grpc-Web": "1",
                "Authorization": f"Bearer {token}",
            }
            
            endpoint = f"{self.url}/clouddrive.CloudDriveFileSrv/CreateFolder"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    endpoint,
                    content=payload,
                    headers=headers
                )
            
            # 检查 gRPC 错误
            grpc_status = response.headers.get("grpc-status", "0")
            if grpc_status != "0":
                grpc_message = unquote(response.headers.get("grpc-message", "Unknown error"))
                logger.error(f"❌ CreateFolder 失败: {grpc_message}")
                return {"success": False, "message": f"CloudDrive 错误: {grpc_message}"}
            
            if response.status_code != 200:
                logger.error(f"❌ CreateFolder 失败: HTTP {response.status_code}")
                return {"success": False, "message": f"HTTP 错误: {response.status_code}"}
            
            # 成功
            logger.info(f"✅ 文件夹创建成功: {path}")
            return {"success": True, "message": "文件夹创建成功"}
        
        except Exception as e:
            logger.error(f"❌ 创建文件夹异常: {e}")
            return {"success": False, "message": str(e)}
    
    async def upload_file_webdav(self, local_file_path: str, remote_path: str, 
                                  file_name: Optional[str] = None) -> Dict[str, Any]:
        """
        通过WebDAV协议上传文件到CloudDrive
        
        CloudDrive2提供WebDAV服务，可以通过PUT请求上传文件
        
        Args:
            local_file_path: 本地文件路径
            remote_path: CloudDrive远程目录路径（如 /115open/Media）
            file_name: 可选的新文件名
            
        Returns:
            {"success": bool, "message": str, "webdav_path": str}
        """
        token = await self.get_token()
        if not token:
            return {"success": False, "message": "无法获取认证 Token"}
        
        try:
            import os
            if not os.path.exists(local_file_path):
                return {"success": False, "message": f"本地文件不存在: {local_file_path}"}
            
            if not file_name:
                file_name = os.path.basename(local_file_path)
            
            # CloudDrive WebDAV路径格式：/dav/挂载点路径
            # 例如：/dav/115open/Media/photo.jpg
            webdav_path = f"/dav{remote_path.rstrip('/')}/{file_name}"
            
            logger.info(f"📤 WebDAV上传: {file_name} -> {webdav_path}")
            
            # 读取文件内容
            with open(local_file_path, 'rb') as f:
                file_content = f.read()
            
            file_size = len(file_content)
            logger.info(f"📦 文件大小: {file_size} bytes")
            
            # 使用PUT请求上传（WebDAV协议）
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/octet-stream",
            }
            
            upload_url = f"{self.url}{webdav_path}"
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.put(
                    upload_url,
                    content=file_content,
                    headers=headers
                )
            
            logger.info(f"📥 WebDAV响应: {response.status_code}")
            
            # WebDAV成功状态码：200 (OK), 201 (Created), 204 (No Content)
            if response.status_code in [200, 201, 204]:
                logger.info(f"✅ WebDAV上传成功: {webdav_path}")
                return {
                    "success": True,
                    "message": "文件上传成功（WebDAV）",
                    "webdav_path": webdav_path
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "message": "WebDAV认证失败，请检查CloudDrive配置"
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "message": f"WebDAV路径不存在: {webdav_path}，请确认CloudDrive已挂载该路径"
                }
            elif response.status_code == 405:
                return {
                    "success": False,
                    "message": "CloudDrive不支持WebDAV PUT上传，可能需要启用WebDAV服务"
                }
            else:
                error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
                return {
                    "success": False,
                    "message": f"WebDAV上传失败: {error_msg}"
                }
        
        except Exception as e:
            logger.error(f"❌ WebDAV上传异常: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": str(e)}
    
    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        删除 CloudDrive 中的文件或文件夹
        
        Args:
            file_path: 要删除的文件/文件夹路径
        """
        token = await self.get_token()
        if not token:
            return {"success": False, "message": "无法获取认证 Token"}
        
        try:
            delete_methods = ["DeleteFile", "DeleteFiles", "RemoveFile", "Delete"]
            
            for method_name in delete_methods:
                try:
                    logger.info(f"🔍 尝试删除方法: {method_name}")
                    result = await self._try_delete_file(method_name, file_path, token)
                    if result["success"]:
                        logger.info(f"✅ 删除成功: {file_path}")
                        return result
                except Exception as e:
                    logger.warning(f"⚠️ 方法 {method_name} 失败: {e}")
                    continue
            
            return {
                "success": False,
                "message": "所有删除方法都失败"
            }
        
        except Exception as e:
            logger.error(f"❌ 删除文件异常: {e}")
            return {"success": False, "message": str(e)}
    
    async def _try_delete_file(self, method_name: str, file_path: str, token: str) -> Dict[str, Any]:
        """尝试使用特定方法删除文件"""
        request = DeleteFileRequest(path=file_path)
        protobuf_bytes = request.SerializeToString()
        payload = self._build_grpc_payload(protobuf_bytes)
        
        headers = {
            "Content-Type": "application/grpc-web",
            "Accept": "*/*",
            "X-User-Agent": "grpc-python/1.0",
            "X-Grpc-Web": "1",
            "Authorization": f"Bearer {token}",
        }
        
        endpoint = f"{self.url}/clouddrive.CloudDriveFileSrv/{method_name}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                endpoint,
                content=payload,
                headers=headers
            )
        
        if response.headers.get("grpc-message"):
            error_msg = unquote(response.headers.get("grpc-message"))
            raise Exception(f"gRPC 错误: {error_msg}")
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        message_bytes = self._parse_grpc_response(response.content)
        result = FileOperationResult()
        result.ParseFromString(message_bytes)
        
        if result.success:
            return {"success": True, "message": "删除成功"}
        else:
            return {"success": False, "message": result.errorMessage}


                }
            elif response.status_code == 405:
                return {
                    "success": False,
                    "message": "CloudDrive不支持WebDAV PUT上传，可能需要启用WebDAV服务"
                }
            else:
                error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
                return {
                    "success": False,
                    "message": f"WebDAV上传失败: {error_msg}"
                }
        
        except Exception as e:
            logger.error(f"❌ WebDAV上传异常: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": str(e)}
    
    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        删除 CloudDrive 中的文件或文件夹
        
        Args:
            file_path: 要删除的文件/文件夹路径
        """
        token = await self.get_token()
        if not token:
            return {"success": False, "message": "无法获取认证 Token"}
        
        try:
            delete_methods = ["DeleteFile", "DeleteFiles", "RemoveFile", "Delete"]
            
            for method_name in delete_methods:
                try:
                    logger.info(f"🔍 尝试删除方法: {method_name}")
                    result = await self._try_delete_file(method_name, file_path, token)
                    if result["success"]:
                        logger.info(f"✅ 删除成功: {file_path}")
                        return result
                except Exception as e:
                    logger.warning(f"⚠️ 方法 {method_name} 失败: {e}")
                    continue
            
            return {
                "success": False,
                "message": "所有删除方法都失败"
            }
        
        except Exception as e:
            logger.error(f"❌ 删除文件异常: {e}")
            return {"success": False, "message": str(e)}
    
    async def _try_delete_file(self, method_name: str, file_path: str, token: str) -> Dict[str, Any]:
        """尝试使用特定方法删除文件"""
        request = DeleteFileRequest(path=file_path)
        protobuf_bytes = request.SerializeToString()
        payload = self._build_grpc_payload(protobuf_bytes)
        
        headers = {
            "Content-Type": "application/grpc-web",
            "Accept": "*/*",
            "X-User-Agent": "grpc-python/1.0",
            "X-Grpc-Web": "1",
            "Authorization": f"Bearer {token}",
        }
        
        endpoint = f"{self.url}/clouddrive.CloudDriveFileSrv/{method_name}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                endpoint,
                content=payload,
                headers=headers
            )
        
        if response.headers.get("grpc-message"):
            error_msg = unquote(response.headers.get("grpc-message"))
            raise Exception(f"gRPC 错误: {error_msg}")
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        message_bytes = self._parse_grpc_response(response.content)
        result = FileOperationResult()
        result.ParseFromString(message_bytes)
        
        if result.success:
            return {"success": True, "message": "删除成功"}
        else:
            return {"success": False, "message": result.errorMessage}
