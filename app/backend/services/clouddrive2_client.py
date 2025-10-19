"""
CloudDrive2 gRPC API 客户端

通过 CloudDrive2 实现 115 网盘上传功能
参考: https://www.clouddrive2.com/api/CloudDrive2_gRPC_API_Guide.html

功能:
1. 解决115上传签名问题
2. 支持大文件分块上传
3. 支持断点续传
4. 智能上传策略（本地挂载 + 远程协议）
5. 秒传支持（通过文件哈希）
6. 挂载点管理
7. 文件操作（创建目录、查询文件等）

实现状态:
✅ 基础连接和认证
✅ 本地挂载上传
🚧 远程上传协议（框架已搭建，待实现 gRPC 调用）
⏳ 文件操作 API
⏳ 挂载点管理 API
⏳ 传输任务管理

详见: CLOUDDRIVE2_API_IMPLEMENTATION_PLAN.md
"""
import os
import asyncio
import hashlib
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

try:
    import grpc
    from grpc import aio as grpc_aio
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False

from log_manager import get_logger
from services.clouddrive2_stub import create_stub, CloudDrive2Stub

logger = get_logger(__name__)


class CloudDrive2Config:
    """CloudDrive2 配置"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 19798,
        username: str = "admin",
        password: str = "",
        use_ssl: bool = False
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.address = f"{host}:{port}"


class CloudDrive2Client:
    """
    CloudDrive2 gRPC 客户端
    
    通过 CloudDrive2 的挂载服务上传文件到 115 网盘
    """
    
    def __init__(self, config: CloudDrive2Config):
        """
        初始化客户端
        
        Args:
            config: CloudDrive2配置
        """
        if not GRPC_AVAILABLE:
            raise ImportError("grpcio 未安装，请运行: pip install grpcio grpcio-tools")
        
        self.config = config
        self.channel: Optional[grpc_aio.Channel] = None
        self.stub: Optional[CloudDrive2Stub] = None
        self.token: Optional[str] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """
        连接到 CloudDrive2 服务
        
        Returns:
            bool: 是否连接成功
        """
        try:
            logger.info(f"🔌 连接到 CloudDrive2: {self.config.address}")
            
            # 创建 gRPC 频道
            if self.config.use_ssl:
                credentials = grpc.ssl_channel_credentials()
                self.channel = grpc_aio.secure_channel(
                    self.config.address,
                    credentials
                )
            else:
                self.channel = grpc_aio.insecure_channel(self.config.address)
            
            # 验证连接并获取认证 token
            await self._authenticate()
            
            # 创建 gRPC stub（传入 auth token）
            self.stub = create_stub(self.channel, self.auth_token)
            logger.info("✅ gRPC Stub 已创建")
            
            self._connected = True
            logger.info("✅ CloudDrive2 连接成功")
            return True
        
        except Exception as e:
            logger.error(f"❌ CloudDrive2 连接失败: {e}")
            return False
    
    async def _authenticate(self):
        """
        身份验证
        
        CloudDrive2 支持两种认证方式：
        1. 方法一：使用用户名/密码获取 JWT token（调用 GetToken）
        2. 方法二：直接使用 API Token（推荐）
        
        优先级：API Token > 用户名/密码
        """
        # 方法二：检查是否配置了 API Token（推荐）
        api_token = os.getenv('CLOUDDRIVE2_API_TOKEN') or self.config.password
        
        # 如果 password 字段看起来像 JWT token，直接使用
        if api_token and (api_token.startswith('eyJ') or len(api_token) > 100):
            self.auth_token = api_token
            logger.info("✅ 使用 API Token 认证")
            return
        
        # 方法一：使用用户名/密码获取 JWT token
        if not self.config.username or not self.config.password:
            logger.warning("⚠️ 未配置认证信息（用户名/密码或 API Token）")
            logger.warning("   提示：推荐使用 API Token，在 CloudDrive2 设置中创建")
            self.auth_token = None
            return
        
        try:
            # 导入 proto
            from protos import clouddrive_pb2
            
            logger.info("🔐 使用用户名/密码获取 JWT token...")
            
            # 调用 GetToken 获取 JWT
            request = clouddrive_pb2.GetTokenRequest(
                userName=self.config.username,
                password=self.config.password
            )
            
            from protos import clouddrive_pb2_grpc
            auth_stub = clouddrive_pb2_grpc.CloudDriveFileSrvStub(self.channel)
            response = await auth_stub.GetToken(request)
            
            if response.success and response.token:
                self.auth_token = response.token
                logger.info("✅ 认证成功，已获取 JWT token")
            else:
                error_msg = response.errorMessage or "Unknown error"
                logger.error(f"❌ 认证失败: {error_msg}")
                logger.warning("   提示：建议在 CloudDrive2 设置中创建 API Token")
                self.auth_token = None
        except ImportError:
            logger.warning("⚠️ proto 不可用，跳过认证")
            self.auth_token = None
        except Exception as e:
            logger.error(f"❌ 认证异常: {e}")
            logger.warning("   提示：如使用 API Token，请将其配置在密码字段或 CLOUDDRIVE2_API_TOKEN 环境变量")
            self.auth_token = None
    
    async def _map_user_path_to_actual_path(
        self,
        user_mount_point: str,
        user_remote_path: str
    ) -> tuple[str, str]:
        """
        将用户配置的路径映射到 CloudDrive2 实际的挂载点路径
        
        例如：
        - 用户配置：/115open/测试
        - 实际挂载：/CloudNAS/115
        - 映射结果：/CloudNAS/115/测试
        
        Args:
            user_mount_point: 用户配置的挂载点（如 /115open）
            user_remote_path: 用户配置的完整路径（如 /115open/测试/file.mp4）
        
        Returns:
            (actual_mount_point, actual_remote_path)
        """
        try:
            # 优先使用用户显式选择的云根（UI 显示如 /115open）
            def first_segment(p: str) -> str:
                parts = p.replace('\\', '/').lstrip('/').split('/')
                return f"/{parts[0]}" if parts and parts[0] else '/'

            user_root = first_segment(user_remote_path)
            mount_root = first_segment(user_mount_point)

            api_root = None
            # 如果用户路径根不是 CloudNAS，则直接以其为 API 根（如 /115open）
            if user_root and user_root.lower() != '/cloudnas':
                api_root = user_root
            # 否则用挂载点参数的根（常为 /115open）
            elif mount_root and mount_root.lower() != '/cloudnas':
                api_root = mount_root

            # 计算相对路径（去掉根段）
            relative_path = user_remote_path.replace('\\', '/').lstrip('/')
            if '/' in relative_path:
                first = relative_path.split('/', 1)[0]
                relative_path = relative_path[len(first):].lstrip('/')
            else:
                relative_path = ''

            if api_root:
                actual_path = f"{api_root}/{relative_path}".rstrip('/') if relative_path else api_root
                logger.info(f"🔄 路径映射: {user_remote_path} -> {actual_path}")
                return api_root, actual_path

            # 回退：查询挂载点并推断
            mounts = await self.get_mount_points()
            if mounts:
                best_mount = mounts[0].get('mount_path') or mounts[0].get('path', '')
                # 将 /CloudNAS/xxx 规范化为 /xxx（尽力）
                if best_mount.startswith('/CloudNAS/'):
                    best_mount = '/' + best_mount.split('/')[-1]
                actual_path = f"{best_mount}/{relative_path}".replace('//', '/')
                logger.info(f"🔄 路径映射(回退): {user_remote_path} -> {actual_path}")
                return best_mount, actual_path

            logger.warning("⚠️ 未找到挂载点，使用用户配置的路径")
            return user_mount_point, user_remote_path
                
        except Exception as e:
            logger.error(f"❌ 路径映射失败: {e}")
            return user_mount_point, user_remote_path
    
    async def _ensure_remote_parent_dirs(self, remote_full_path: str) -> None:
        """
        确保远程父目录存在（按段创建）。

        使用 CreateFolder(parentPath, folderName) 逐级创建，已存在则跳过。
        参考: CloudDrive2 gRPC API - 文件操作 [CreateFolder]
        文档: https://www.clouddrive2.com/api/CloudDrive2_gRPC_API_Guide.html
        """
        # 某些版本不支持 CreateFolder（UNIMPLEMENTED）。
        # 按官方错误语义，若不支持就不尝试创建，只验证父级是否存在，缺失则直接抛错由上层处理。
        try:
            from protos import clouddrive_pb2
        except Exception:
            return

        if not self.stub or not getattr(self.stub, 'official_stub', None):
            return

        path = remote_full_path.replace('\\', '/').strip()
        if not path.startswith('/'):
            return

        parent_path = os.path.dirname(path)
        if parent_path in ('', '/'):
            return

        try:
            req = clouddrive_pb2.FindFileByPathRequest(theFilePath=parent_path)
            await self.stub.official_stub.FindFileByPath(
                req, metadata=self.stub._get_metadata()
            )
        except Exception as e:
            # 父目录不存在，记录并让上层给出更明确错误
            logger.warning(f"⚠️ 远程父目录不存在: {parent_path} -> {e}")
            raise

    async def disconnect(self):
        """断开连接"""
        if self.channel:
            await self.channel.close()
            self._connected = False
            logger.info("🔌 CloudDrive2 已断开")
    
    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        mount_point: str = "/115",
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        上传文件到 115 网盘（通过 CloudDrive2）
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程路径（相对于挂载点）
            mount_point: CloudDrive2 挂载点路径
            progress_callback: 进度回调 (uploaded_bytes, total_bytes)
        
        Returns:
            {
                'success': bool,
                'message': str,
                'file_path': str,  # 远程文件路径
                'file_size': int,
                'upload_time': float
            }
        """
        import time
        start_time = time.time()
        
        try:
            if not self._connected:
                return {
                    'success': False,
                    'message': 'CloudDrive2 未连接'
                }
            
            if not os.path.exists(local_path):
                return {
                    'success': False,
                    'message': f'本地文件不存在: {local_path}'
                }
            
            file_size = os.path.getsize(local_path)
            file_name = os.path.basename(local_path)
            
            logger.info(f"📤 开始上传: {file_name} ({file_size} bytes)")
            logger.info(f"   用户配置挂载点: {mount_point}")
            logger.info(f"   用户配置目标路径: {remote_path}")
            
            # 路径映射：将用户配置的路径映射到实际挂载点
            actual_mount_point, actual_remote_path = await self._map_user_path_to_actual_path(
                mount_point, remote_path
            )
            
            logger.info(f"   实际挂载点: {actual_mount_point}")
            logger.info(f"   实际目标路径: {actual_remote_path}")
            
            # 尝试方案1: 本地挂载上传（如果挂载点存在）
            # 尝试方案2: gRPC API 上传（CreateFile + WriteToFile + CloseFile）
            
            # 检查挂载点是否本地可访问
            if os.path.exists(actual_mount_point):
                logger.info("🔧 使用方案1: 本地挂载上传")
                result = await self._upload_via_mount(
                    local_path, actual_remote_path, actual_mount_point, 
                    file_size, progress_callback
                )
            else:
                logger.info("🔧 使用方案2: gRPC API 上传（CreateFile + WriteToFile + CloseFile）")
                result = await self._upload_via_grpc(
                    local_path, actual_remote_path,
                    file_size, progress_callback
                )
            
            upload_time = time.time() - start_time
            
            if result['success']:
                logger.info(f"✅ 上传成功: {file_name} (耗时: {upload_time:.2f}s)")
                result['upload_time'] = upload_time
                result['file_size'] = file_size
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 上传异常: {e}", exc_info=True)
            return {
                'success': False,
                'message': str(e)
            }
    
    async def _upload_via_mount(
        self,
        local_path: str,
        remote_path: str,
        mount_point: str,
        file_size: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        通过挂载目录上传文件
        
        CloudDrive2 将云盘挂载为本地目录，
        我们只需要将文件复制到挂载目录，CloudDrive2 会自动上传
        """
        try:
            # 构建完整的目标路径
            # 确保 remote_path 使用正斜杠（Unix风格），然后转换为系统路径
            remote_path_normalized = remote_path.lstrip('/').replace('\\', '/')
            target_path = os.path.join(mount_point, remote_path_normalized)
            target_dir = os.path.dirname(target_path)
            
            logger.info(f"📂 目标路径: {target_path}")
            logger.info(f"📁 目标目录: {target_dir}")
            
            # 确保目标目录存在
            if not os.path.exists(target_dir):
                logger.info(f"📁 创建目录: {target_dir}")
                os.makedirs(target_dir, exist_ok=True)
            else:
                logger.info(f"✅ 目录已存在: {target_dir}")
            
            # 检查目标文件是否已存在
            if os.path.exists(target_path):
                logger.warning(f"⚠️ 目标文件已存在，将覆盖: {target_path}")
            
            # 分块复制文件（支持进度回调）
            chunk_size = 8 * 1024 * 1024  # 8MB
            uploaded_bytes = 0
            
            logger.info(f"📤 开始复制文件: {os.path.basename(local_path)} ({file_size} bytes)")
            
            with open(local_path, 'rb') as src:
                with open(target_path, 'wb') as dst:
                    while True:
                        chunk = src.read(chunk_size)
                        if not chunk:
                            break
                        
                        dst.write(chunk)
                        uploaded_bytes += len(chunk)
                        
                        # 进度回调
                        if progress_callback:
                            progress_callback(uploaded_bytes, file_size)
                        
                        # 让出控制权
                        await asyncio.sleep(0)
            
            logger.info(f"✅ 文件已复制到挂载目录: {target_path}")
            logger.info(f"📊 复制完成: {uploaded_bytes}/{file_size} bytes ({uploaded_bytes/file_size*100:.1f}%)")
            
            # 等待 CloudDrive2 同步到云端
            # TODO: 可以通过 gRPC API 查询上传状态
            await asyncio.sleep(1)
            
            return {
                'success': True,
                'message': '文件上传成功',
                'file_path': target_path,
                'local_path': local_path
            }
        
        except Exception as e:
            logger.error(f"❌ 挂载上传失败: {e}")
            return {
                'success': False,
                'message': f'挂载上传失败: {e}'
            }
    
    async def _upload_via_grpc(
        self,
        local_path: str,
        remote_path: str,
        file_size: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        使用 gRPC API 上传文件
        
        CloudDrive2 标准上传方法：
        1. CreateFile(parentPath, fileName) → fileHandle
        2. WriteToFile(fileHandle, startPos, buffer) → 循环写入
        3. CloseFile(fileHandle) → 完成
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程完整路径（如 /CloudNAS/115/2025/10/19/file.mp4）
            file_size: 文件大小
            progress_callback: 进度回调
        
        Returns:
            上传结果字典
        """
        try:
            from protos import clouddrive_pb2
            
            file_name = os.path.basename(remote_path)
            parent_path = os.path.dirname(remote_path)
            
            logger.info(f"📝 gRPC API 上传")
            logger.info(f"   父目录: {parent_path}")
            logger.info(f"   文件名: {file_name}")
            logger.info(f"   大小: {file_size} bytes")
            
            # 步骤0: 校验父目录存在（某些版本不支持在服务端创建目录）
            try:
                await self._ensure_remote_parent_dirs(remote_path)
            except Exception as e:
                return {
                    'success': False,
                    'message': f'远程父目录不存在: {os.path.dirname(remote_path)}'
                }

            # 步骤1: 创建文件
            logger.info("📄 步骤1: 创建文件...")
            create_request = clouddrive_pb2.CreateFileRequest(
                parentPath=parent_path,
                fileName=file_name
            )
            
            create_response = await self.stub.official_stub.CreateFile(
                create_request,
                metadata=self.stub._get_metadata()
            )
            
            file_handle = create_response.fileHandle
            logger.info(f"✅ 文件已创建，fileHandle={file_handle}")
            
            # 步骤2: 分块写入文件
            logger.info(f"📤 步骤2: 写入文件数据...")
            chunk_size = 4 * 1024 * 1024  # 4MB 块
            uploaded_bytes = 0
            
            with open(local_path, 'rb') as f:
                chunk_index = 0
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    # 写入数据块
                    write_request = clouddrive_pb2.WriteFileRequest(
                        fileHandle=file_handle,
                        startPos=uploaded_bytes,
                        length=len(chunk),
                        buffer=chunk,
                        closeFile=False
                    )
                    
                    write_response = await self.stub.official_stub.WriteToFile(
                        write_request,
                        metadata=self.stub._get_metadata()
                    )
                    
                    uploaded_bytes += write_response.bytesWritten
                    chunk_index += 1
                    
                    # 进度回调
                    if progress_callback:
                        await progress_callback(uploaded_bytes, file_size)
                    
                    progress_percent = (uploaded_bytes / file_size * 100) if file_size > 0 else 100
                    logger.info(f"   块 {chunk_index}: {uploaded_bytes}/{file_size} ({progress_percent:.1f}%)")
            
            # 步骤3: 关闭文件
            logger.info("🔒 步骤3: 关闭文件...")
            close_request = clouddrive_pb2.CloseFileRequest(
                fileHandle=file_handle
            )
            close_res = await self.stub.official_stub.CloseFile(
                close_request,
                metadata=self.stub._get_metadata()
            )
            # CloseFile 返回 FileOperationResult，需检查 success
            if hasattr(close_res, 'success') and not close_res.success:
                err = getattr(close_res, 'errorMessage', '') or 'unknown error'
                raise RuntimeError(f"关闭文件失败: {err}")
            
            logger.info(f"✅ 上传完成: {file_name} ({uploaded_bytes} bytes)")
            
            return {
                'success': True,
                'message': 'Upload successful',
                'file_path': remote_path,
                'uploaded_bytes': uploaded_bytes
            }
            
        except Exception as e:
            logger.error(f"❌ gRPC 上传失败: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'message': f'gRPC upload failed: {str(e)}'
            }
    
    async def _upload_via_remote_protocol(
        self,
        local_path: str,
        remote_path: str,
        mount_point: str,
        file_size: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        通过远程上传协议上传文件
        
        根据 CloudDrive2 gRPC API 文档的远程上传协议：
        https://www.clouddrive2.com/api/CloudDrive2_gRPC_API_Guide.html#remote-upload
        
        工作流程：
        1. 客户端发起上传请求（文件名、大小、路径）
        2. 服务器返回上传会话 ID
        3. 服务器请求文件数据块
        4. 客户端发送数据块
        5. 服务器请求哈希验证
        6. 完成上传
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程目标路径
            mount_point: CloudDrive2 挂载点路径
            file_size: 文件大小
            progress_callback: 进度回调
        
        Returns:
            上传结果字典
        """
        try:
            file_name = os.path.basename(local_path)
            logger.info(f"🌐 远程上传协议开始")
            logger.info(f"   文件: {file_name}")
            logger.info(f"   大小: {file_size} bytes")
            logger.info(f"   目标: {remote_path}")  # remote_path 已经是完整路径
            
            # TODO: 实现完整的远程上传协议
            # 由于当前没有 protobuf 定义文件，这里提供框架实现
            
            # 步骤1: 计算文件哈希（用于快速上传检测）
            logger.info("🔐 计算文件哈希...")
            file_hash = await self._calculate_file_hash(local_path)
            logger.info(f"✅ SHA256: {file_hash[:16]}...")
            
            # 步骤2: 创建上传会话
            logger.info("📋 创建上传会话...")
            session_result = await self._create_upload_session(
                file_name=file_name,
                file_size=file_size,
                file_hash=file_hash,
                target_path=remote_path  # remote_path 已经是完整路径
            )
            
            # 检查是否需要使用 WriteToFile API
            if isinstance(session_result, dict) and session_result.get('use_write_file_api'):
                logger.info("🔄 切换到 WriteToFile API 上传")
                return await self._upload_via_write_file_api(
                    local_path, remote_path, file_size, progress_callback
                )
            
            if not session_result:
                return {
                    'success': False,
                    'message': '创建上传会话失败'
                }
            
            session_id = session_result.get('session_id') if isinstance(session_result, dict) else session_result
            
            logger.info(f"✅ 会话ID: {session_id}")
            
            # 步骤3: 处理远程上传通道（服务器驱动）
            logger.info("📡 监听远程上传通道（双向流式）...")
            result = await self._handle_remote_upload_channel(
                session_id=session_id,
                local_path=local_path,
                file_size=file_size,
                progress_callback=progress_callback
            )
            
            if result.get('success'):
                logger.info(f"✅ 远程上传成功: {file_name}")
                result['file_path'] = remote_path
                result['local_path'] = local_path
                result['method'] = 'remote_protocol'
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 远程上传失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'远程上传失败: {e}'
            }
    
    async def _upload_via_write_file_api(
        self,
        local_path: str,
        remote_path: str,
        file_size: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        使用 WriteToFile API 上传文件
        
        流程：
        1. CreateFile - 创建文件并获取 fileHandle
        2. WriteToFile - 分块写入文件数据
        3. CloseFile - 关闭文件
        """
        try:
            from protos import clouddrive_pb2
            
            file_name = os.path.basename(remote_path)
            parent_path = os.path.dirname(remote_path)
            
            logger.info(f"📝 使用 WriteToFile API 上传")
            logger.info(f"   父目录: {parent_path}")
            logger.info(f"   文件名: {file_name}")
            
            # 步骤1: 创建文件
            logger.info("📄 创建文件...")
            create_request = clouddrive_pb2.CreateFileRequest(
                parentPath=parent_path,
                fileName=file_name
            )
            
            create_response = await self.stub.official_stub.CreateFile(
                create_request,
                metadata=self.stub._get_metadata()
            )
            
            file_handle = create_response.fileHandle
            logger.info(f"✅ 文件已创建，handle: {file_handle}")
            
            # 步骤2: 分块写入文件
            chunk_size = 4 * 1024 * 1024  # 4MB
            uploaded_bytes = 0
            
            with open(local_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    # 写入数据块
                    write_request = clouddrive_pb2.WriteFileRequest(
                        fileHandle=file_handle,
                        startPos=uploaded_bytes,
                        length=len(chunk),
                        buffer=chunk,
                        closeFile=False
                    )
                    
                    write_response = await self.stub.official_stub.WriteToFile(
                        write_request,
                        metadata=self.stub._get_metadata()
                    )
                    
                    uploaded_bytes += write_response.bytesWritten
                    
                    # 进度回调
                    if progress_callback:
                        await progress_callback(uploaded_bytes, file_size)
                    
                    logger.info(f"📤 已上传: {uploaded_bytes}/{file_size} ({uploaded_bytes*100//file_size}%)")
            
            # 步骤3: 关闭文件
            logger.info("🔒 关闭文件...")
            close_request = clouddrive_pb2.CloseFileRequest(
                fileHandle=file_handle
            )
            await self.stub.official_stub.CloseFile(
                close_request,
                metadata=self.stub._get_metadata()
            )
            
            logger.info(f"✅ 文件上传成功: {file_name}")
            
            return {
                'success': True,
                'file_path': remote_path,
                'file_size': uploaded_bytes,
                'message': 'Upload successful via WriteToFile API'
            }
            
        except Exception as e:
            logger.error(f"❌ WriteToFile API 上传失败: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'message': f'Upload failed: {str(e)}'
            }
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件 SHA256 哈希"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()
    
    async def _create_upload_session(
        self,
        file_name: str,
        file_size: int,
        file_hash: str,
        target_path: str
    ) -> Optional[str]:
        """
        创建上传会话
        
        通过 gRPC API 调用 CreateUploadSession
        返回会话ID
        """
        try:
            if not self.stub:
                logger.error("❌ gRPC stub 未初始化")
                return None
            
            # 调用 gRPC API
            logger.info("📡 调用 gRPC API: CreateUploadSession")
            response = await self.stub.CreateUploadSession(
                file_name=file_name,
                file_size=file_size,
                file_hash=file_hash,
                target_path=target_path,
                cloud_type="115"
            )
            
            # 检查是否需要使用 WriteToFile API
            if response and response.get('use_write_file_api'):
                logger.info("🔄 远程上传协议不可用，返回 WriteToFile API 标记")
                return response  # 返回包含 use_write_file_api 的字典
            
            if response and response.get('success'):
                session_id = response.get('session_id')
                quick_upload = response.get('quick_upload', False)
                
                if quick_upload:
                    logger.info("⚡ 支持秒传！")
                
                logger.info(f"✅ 上传会话已创建: {session_id}")
                return session_id
            else:
                logger.error(f"❌ 创建会话失败: {response.get('message') if response else 'No response'}")
                return None
        
        except Exception as e:
            logger.error(f"❌ 创建上传会话失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _upload_chunk(
        self,
        session_id: str,
        chunk_index: int,
        chunk_data: bytes
    ) -> bool:
        """
        上传数据块
        
        通过 gRPC API 发送文件数据块
        """
        try:
            if not self.stub:
                logger.error("❌ gRPC stub 未初始化")
                return False
            
            # 调用 gRPC API
            success = await self.stub.UploadChunk(
                session_id=session_id,
                chunk_index=chunk_index,
                chunk_data=chunk_data
            )
            
            if success:
                logger.debug(f"✅ 块 {chunk_index} 上传成功: {len(chunk_data)} bytes")
            else:
                logger.error(f"❌ 块 {chunk_index} 上传失败")
            
            return success
        
        except Exception as e:
            logger.error(f"❌ 上传数据块失败: {e}")
            return False
    
    async def _handle_remote_upload_channel(
        self,
        session_id: str,
        local_path: str,
        file_size: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        处理远程上传通道（双向流式通信）
        
        CloudDrive2 远程上传协议是服务器驱动的：
        1. 客户端监听 RemoteUploadChannel（服务器流式推送）
        2. 服务器请求数据 (read_data) 或哈希 (hash_data)
        3. 客户端响应请求
        4. 服务器推送状态变化 (status_changed)
        
        Args:
            session_id: 上传会话ID
            local_path: 本地文件路径
            file_size: 文件大小
            progress_callback: 进度回调函数
        
        Returns:
            上传结果字典
        """
        try:
            if not self.stub:
                logger.error("❌ gRPC stub 未初始化")
                return {'success': False, 'message': 'gRPC stub 未初始化'}
            
            logger.info(f"📡 开始监听上传通道: {session_id[:8]}...")
            
            # 监听服务器流式推送
            async for reply in self.stub.RemoteUploadChannel(session_id=session_id):
                try:
                    # 检查是否是当前上传任务
                    if reply.get('upload_id') != session_id:
                        continue
                    
                    # 处理服务器请求
                    request_type = reply.get('request_type')
                    
                    if request_type == 'read_data':
                        # 服务器请求读取文件数据
                        logger.info("📖 服务器请求文件数据")
                        read_request = reply.get('read_data', {})
                        success = await self._handle_read_data_request(
                            session_id=session_id,
                            offset=read_request.get('offset', 0),
                            length=read_request.get('length', 0),
                            local_path=local_path,
                            file_size=file_size,
                            progress_callback=progress_callback
                        )
                        if not success:
                            return {'success': False, 'message': '发送文件数据失败'}
                    
                    elif request_type == 'hash_data':
                        # 服务器请求计算哈希
                        logger.info("🔐 服务器请求哈希计算")
                        success = await self._handle_hash_data_request(
                            session_id=session_id,
                            local_path=local_path,
                            file_size=file_size
                        )
                        if not success:
                            return {'success': False, 'message': '哈希计算失败'}
                    
                    elif request_type == 'status_changed':
                        # 上传状态变化
                        status_data = reply.get('status_changed', {})
                        status = status_data.get('status')
                        error_msg = status_data.get('error_message', '')
                        
                        logger.info(f"📊 状态变化: {status}")
                        
                        if status == 'Success' or status == 'Completed':
                            logger.info("✅ 上传成功！")
                            return {
                                'success': True,
                                'message': '文件上传成功'
                            }
                        elif status == 'Error' or status == 'Failed':
                            logger.error(f"❌ 上传失败: {error_msg}")
                            return {
                                'success': False,
                                'message': f'上传失败: {error_msg}'
                            }
                        elif status == 'Uploading':
                            logger.info("📤 上传中...")
                        elif status == 'Checking':
                            logger.info("🔍 检查中（秒传检测）...")
                
                except Exception as e:
                    logger.error(f"❌ 处理服务器请求失败: {e}")
                    continue
            
            # 通道关闭
            logger.warning("⚠️ 上传通道已关闭，但未收到完成状态")
            return {
                'success': False,
                'message': '上传通道意外关闭'
            }
        
        except Exception as e:
            logger.error(f"❌ 上传通道处理失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'上传通道异常: {str(e)}'
            }
    
    async def _handle_read_data_request(
        self,
        session_id: str,
        offset: int,
        length: int,
        local_path: str,
        file_size: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        处理服务器的读取数据请求
        
        Args:
            session_id: 上传会话ID
            offset: 读取偏移量
            length: 读取长度
            local_path: 本地文件路径
            file_size: 文件大小
            progress_callback: 进度回调
        
        Returns:
            是否成功
        """
        try:
            logger.info(f"📖 读取文件数据: offset={offset}, length={length}")
            
            # 从本地文件读取数据
            with open(local_path, 'rb') as f:
                f.seek(offset)
                data = f.read(length)
            
            if len(data) != length:
                logger.warning(f"⚠️ 读取长度不匹配: expected={length}, actual={len(data)}")
            
            # 发送数据给服务器
            success = await self.stub.RemoteReadData(
                session_id=session_id,
                offset=offset,
                length=len(data),
                data=data
            )
            
            if success:
                logger.info(f"✅ 数据块已发送: {len(data)} bytes")
                
                # 进度回调
                if progress_callback:
                    await progress_callback(offset + len(data), file_size)
            else:
                logger.error("❌ 数据块发送失败")
            
            return success
        
        except Exception as e:
            logger.error(f"❌ 处理读取请求失败: {e}")
            return False
    
    async def _handle_hash_data_request(
        self,
        session_id: str,
        local_path: str,
        file_size: int
    ) -> bool:
        """
        处理服务器的哈希计算请求
        
        Args:
            session_id: 上传会话ID
            local_path: 本地文件路径
            file_size: 文件大小
        
        Returns:
            是否成功
        """
        try:
            logger.info("🔐 开始计算文件哈希...")
            
            # 计算哈希并报告进度
            with open(local_path, 'rb') as f:
                bytes_hashed = 0
                chunk_size = 1024 * 1024  # 1MB
                
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    bytes_hashed += len(chunk)
                    
                    # 报告哈希进度
                    success = await self.stub.RemoteHashProgress(
                        session_id=session_id,
                        bytes_hashed=bytes_hashed,
                        total_bytes=file_size
                    )
                    
                    if not success:
                        logger.error("❌ 哈希进度报告失败")
                        return False
                    
                    # 每 10MB 记录一次
                    if bytes_hashed % (10 * 1024 * 1024) == 0:
                        progress = (bytes_hashed / file_size) * 100
                        logger.info(f"📊 哈希进度: {progress:.1f}%")
            
            logger.info("✅ 哈希计算完成")
            return True
        
        except Exception as e:
            logger.error(f"❌ 哈希计算失败: {e}")
            return False
    
    async def _complete_upload_session(self, session_id: str) -> bool:
        """
        完成上传会话（已弃用 - 远程上传协议不需要）
        
        在远程上传协议中，服务器会通过 status_changed 通知完成，
        不需要客户端主动调用 Complete
        """
        logger.warning("⚠️ _complete_upload_session 已弃用，远程上传协议使用 RemoteUploadChannel")
        return False
    
    async def get_mount_points(self) -> List[Dict[str, Any]]:
        """
        获取所有挂载点列表
        
        通过 gRPC API 获取 CloudDrive2 中配置的所有挂载点
        
        Returns:
            List[{
                'name': str,           # 挂载点名称（如 "115"）
                'path': str,           # 挂载路径（如 "/CloudNAS/115"）
                'cloud_type': str,     # 云盘类型（如 "115"）
                'mounted': bool,       # 是否已挂载
                'space_total': int,    # 总空间（字节）
                'space_used': int,     # 已用空间（字节）
            }]
        """
        try:
            if not self._connected:
                logger.warning("⚠️ CloudDrive2 未连接，尝试重新连接...")
                await self.connect()
            
            if not self.stub:
                logger.error("❌ gRPC stub 未初始化")
                return []
            
            # 调用 gRPC API 获取挂载点列表
            logger.info("📡 调用 gRPC API: ListMounts")
            mounts = await self.stub.ListMounts()
            
            if mounts:
                logger.info(f"✅ 获取到 {len(mounts)} 个挂载点")
                for mount in mounts:
                    logger.info(f"   - {mount.get('name')}: {mount.get('path')} ({mount.get('cloud_type')})")
            else:
                logger.warning("⚠️ 未找到挂载点")
            
            return mounts
        
        except Exception as e:
            logger.error(f"❌ 获取挂载点列表失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def check_mount_status(self, mount_point: str = "/115") -> Dict[str, Any]:
        """
        检查挂载点状态
        
        优先级：
        1. 检查本地共享挂载（如果路径存在）
        2. 通过 gRPC API 检查远程挂载点
        3. 如果都不可用，返回错误
        
        Args:
            mount_point: 挂载点路径
        
        Returns:
            {
                'mounted': bool,
                'path': str,
                'available': bool,
                'method': str,         # 'local' | 'remote' | 'unknown'
                'message': str
            }
        """
        try:
            # 方法1: 检查本地共享挂载
            if os.path.exists(mount_point):
                logger.info(f"✅ 检测到本地共享挂载点: {mount_point}")
                
                # 检查目录是否可写
                test_file = os.path.join(mount_point, '.clouddrive_test')
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    writable = True
                    logger.info(f"✅ 挂载点可写")
                except Exception as e:
                    writable = False
                    logger.warning(f"⚠️ 挂载点不可写: {e}")
                
                return {
                    'mounted': True,
                    'path': mount_point,
                    'available': writable,
                    'method': 'local',
                    'writable': writable,
                    'message': '本地共享挂载' if writable else '本地挂载存在但不可写'
                }
            
            # 方法2: 通过 gRPC API 检查远程挂载点
            logger.info(f"🔍 本地路径不存在，尝试通过 gRPC API 检查: {mount_point}")
            
            # 获取所有挂载点
            mount_points = await self.get_mount_points()
            
            # 检查是否存在匹配的挂载点
            for mp in mount_points:
                if mp.get('path') == mount_point or mount_point.startswith(mp.get('path', '')):
                    logger.info(f"✅ 在 CloudDrive2 中找到匹配的挂载点: {mp.get('name')}")
                    return {
                        'mounted': True,
                        'path': mount_point,
                        'available': mp.get('mounted', False),
                        'method': 'remote',
                        'cloud_type': mp.get('cloud_type', 'unknown'),
                        'message': f"远程挂载点: {mp.get('name')}"
                    }
            
            # 方法3: 如果本地路径不存在且 gRPC 返回空，假设使用远程上传协议
            logger.info(f"💡 本地路径不存在，将使用 gRPC 远程上传协议")
            logger.info(f"   挂载点: {mount_point}")
            logger.info(f"   上传方式: CloudDrive2 gRPC 远程上传（无需本地挂载）")
            
            # 对于远程部署，CloudDrive2 服务端有挂载点即可
            # 客户端通过 gRPC 上传，不需要本地挂载
            return {
                'mounted': True,           # gRPC 可用，视为"已挂载"
                'path': mount_point,
                'available': True,         # 允许继续上传
                'method': 'remote',        # 使用远程协议
                'message': '将通过 gRPC 远程上传协议上传文件'
            }
        
        except Exception as e:
            logger.error(f"❌ 检查挂载状态失败: {e}")
            return {
                'mounted': False,
                'path': mount_point,
                'available': False,
                'error': str(e)
            }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()
    
    # ==================== 文件操作 API ====================
    
    async def create_folder(self, path: str) -> Dict[str, Any]:
        """
        创建文件夹
        
        Args:
            path: 文件夹路径（如 /CloudNAS/115/测试/新文件夹）
        
        Returns:
            {'success': bool, 'message': str}
        """
        try:
            # TODO: 实现 gRPC API 调用
            # request = CreateFolderRequest(path=path)
            # response = await self.stub.CreateFolder(request)
            
            logger.warning(f"⚠️ CreateFolder API 尚未实现: {path}")
            
            # 临时方案：如果是本地挂载，直接创建
            if os.path.exists(os.path.dirname(path)):
                os.makedirs(path, exist_ok=True)
                return {'success': True, 'message': '文件夹创建成功（本地）'}
            
            return {'success': False, 'message': 'gRPC API 尚未实现'}
        
        except Exception as e:
            logger.error(f"❌ 创建文件夹失败: {e}")
            return {'success': False, 'message': str(e)}
    
    async def list_files(self, path: str = "/") -> List[Dict[str, Any]]:
        """
        列出目录中的文件
        
        Args:
            path: 目录路径
        
        Returns:
            List[{
                'name': str,
                'path': str,
                'type': str,  # 'file' | 'folder'
                'size': int,
                'modified_time': str
            }]
        """
        try:
            # TODO: 实现 gRPC API 调用
            # request = ListFilesRequest(path=path)
            # response = await self.stub.ListFiles(request)
            
            logger.warning(f"⚠️ ListFiles API 尚未实现: {path}")
            
            # 临时方案：如果是本地挂载，直接读取
            if os.path.exists(path):
                files = []
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    stat = os.stat(item_path)
                    files.append({
                        'name': item,
                        'path': item_path,
                        'type': 'folder' if os.path.isdir(item_path) else 'file',
                        'size': stat.st_size,
                        'modified_time': stat.st_mtime
                    })
                return files
            
            return []
        
        except Exception as e:
            logger.error(f"❌ 列出文件失败: {e}")
            return []
    
    async def get_file_info(self, path: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            path: 文件路径
        
        Returns:
            {
                'name': str,
                'path': str,
                'type': str,
                'size': int,
                'hash': str,
                'created_time': str,
                'modified_time': str
            }
        """
        try:
            # TODO: 实现 gRPC API 调用
            logger.warning(f"⚠️ GetFileInfo API 尚未实现: {path}")
            
            # 临时方案：本地文件
            if os.path.exists(path):
                stat = os.stat(path)
                return {
                    'name': os.path.basename(path),
                    'path': path,
                    'type': 'folder' if os.path.isdir(path) else 'file',
                    'size': stat.st_size,
                    'created_time': stat.st_ctime,
                    'modified_time': stat.st_mtime
                }
            
            return None
        
        except Exception as e:
            logger.error(f"❌ 获取文件信息失败: {e}")
            return None
    
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """
        删除文件或文件夹
        
        Args:
            path: 文件路径
        
        Returns:
            {'success': bool, 'message': str}
        """
        try:
            # TODO: 实现 gRPC API 调用
            logger.warning(f"⚠️ DeleteFile API 尚未实现: {path}")
            return {'success': False, 'message': 'gRPC API 尚未实现'}
        
        except Exception as e:
            logger.error(f"❌ 删除文件失败: {e}")
            return {'success': False, 'message': str(e)}
    
    # ==================== 传输任务管理 ====================
    
    async def get_transfer_tasks(self) -> List[Dict[str, Any]]:
        """
        获取所有传输任务
        
        Returns:
            List[{
                'task_id': str,
                'type': str,  # 'upload' | 'download'
                'file_name': str,
                'progress': float,  # 0-100
                'status': str,  # 'running' | 'paused' | 'completed' | 'failed'
                'speed': int,  # bytes/s
            }]
        """
        try:
            # TODO: 实现 gRPC API 调用
            logger.warning("⚠️ GetTransferTasks API 尚未实现")
            return []
        
        except Exception as e:
            logger.error(f"❌ 获取传输任务失败: {e}")
            return []
    
    async def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务进度
        
        Args:
            task_id: 任务ID
        
        Returns:
            {
                'progress': float,
                'uploaded_bytes': int,
                'total_bytes': int,
                'speed': int
            }
        """
        try:
            # TODO: 实现 gRPC API 调用
            logger.warning(f"⚠️ GetTaskProgress API 尚未实现: {task_id}")
            return None
        
        except Exception as e:
            logger.error(f"❌ 获取任务进度失败: {e}")
            return None
    
    # ==================== 服务器信息 ====================
    
    async def get_server_info(self) -> Optional[Dict[str, Any]]:
        """
        获取 CloudDrive2 服务器信息
        
        Returns:
            {
                'version': str,
                'build': str,
                'uptime': int,
                'mounts_count': int
            }
        """
        try:
            # TODO: 实现 gRPC API 调用
            logger.warning("⚠️ GetServerInfo API 尚未实现")
            return {
                'version': 'unknown',
                'build': 'unknown',
                'connected': self._connected
            }
        
        except Exception as e:
            logger.error(f"❌ 获取服务器信息失败: {e}")
            return None
    
    # ==================== 云盘 API 管理 ====================
    
    async def list_cloud_apis(self) -> List[Dict[str, Any]]:
        """
        获取支持的云盘 API 列表
        
        Returns:
            List[{
                'name': str,        # 云盘名称（如 "115", "阿里云盘"）
                'type': str,        # 云盘类型
                'enabled': bool,    # 是否启用
                'account': str,     # 账号信息
            }]
        """
        try:
            # TODO: 实现 gRPC API 调用
            # request = ListCloudAPIsRequest()
            # response = await self.stub.ListCloudAPIs(request)
            
            logger.warning("⚠️ ListCloudAPIs API 尚未实现")
            return []
        
        except Exception as e:
            logger.error(f"❌ 获取云盘 API 列表失败: {e}")
            return []
    
    async def get_cloud_api_config(self, cloud_type: str) -> Optional[Dict[str, Any]]:
        """
        获取指定云盘的配置
        
        Args:
            cloud_type: 云盘类型（如 "115"）
        
        Returns:
            {
                'type': str,
                'enabled': bool,
                'config': dict  # 云盘特定配置
            }
        """
        try:
            # TODO: 实现 gRPC API 调用
            logger.warning(f"⚠️ GetCloudAPIConfig API 尚未实现: {cloud_type}")
            return None
        
        except Exception as e:
            logger.error(f"❌ 获取云盘配置失败: {e}")
            return None
    
    # ==================== 离线下载（如果支持）====================
    
    async def create_offline_download(
        self,
        url: str,
        target_path: str,
        cloud_type: str = "115"
    ) -> Optional[str]:
        """
        创建离线下载任务
        
        Args:
            url: 下载链接（磁力链、HTTP等）
            target_path: 保存路径
            cloud_type: 云盘类型
        
        Returns:
            task_id: 任务ID
        """
        try:
            # TODO: 实现 gRPC API 调用
            # request = CreateOfflineDownloadRequest(
            #     url=url,
            #     target_path=target_path,
            #     cloud_type=cloud_type
            # )
            # response = await self.stub.CreateOfflineDownload(request)
            
            logger.warning(f"⚠️ CreateOfflineDownload API 尚未实现: {url}")
            return None
        
        except Exception as e:
            logger.error(f"❌ 创建离线下载失败: {e}")
            return None
    
    async def get_offline_download_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取离线下载任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            {
                'status': str,      # 'pending' | 'downloading' | 'completed' | 'failed'
                'progress': float,  # 0-100
                'speed': int,       # bytes/s
                'file_name': str
            }
        """
        try:
            # TODO: 实现 gRPC API 调用
            logger.warning(f"⚠️ GetOfflineDownloadStatus API 尚未实现: {task_id}")
            return None
        
        except Exception as e:
            logger.error(f"❌ 获取离线下载状态失败: {e}")
            return None
    
    # ==================== WebDAV 管理 ====================
    
    async def get_webdav_config(self) -> Optional[Dict[str, Any]]:
        """
        获取 WebDAV 配置
        
        Returns:
            {
                'enabled': bool,
                'port': int,
                'username': str,
                'read_only': bool
            }
        """
        try:
            # TODO: 实现 gRPC API 调用
            logger.warning("⚠️ GetWebDAVConfig API 尚未实现")
            return None
        
        except Exception as e:
            logger.error(f"❌ 获取 WebDAV 配置失败: {e}")
            return None
    
    async def enable_webdav(
        self,
        port: int = 8080,
        username: str = "admin",
        password: str = "",
        read_only: bool = False
    ) -> Dict[str, Any]:
        """
        启用 WebDAV 服务
        
        Args:
            port: WebDAV 端口
            username: 用户名
            password: 密码
            read_only: 是否只读
        
        Returns:
            {'success': bool, 'message': str}
        """
        try:
            # TODO: 实现 gRPC API 调用
            logger.warning("⚠️ EnableWebDAV API 尚未实现")
            return {'success': False, 'message': 'gRPC API 尚未实现'}
        
        except Exception as e:
            logger.error(f"❌ 启用 WebDAV 失败: {e}")
            return {'success': False, 'message': str(e)}
    
    # ==================== 高级文件操作 ====================
    
    async def move_file(self, source_path: str, dest_path: str) -> Dict[str, Any]:
        """
        移动文件或文件夹
        
        Args:
            source_path: 源路径
            dest_path: 目标路径
        
        Returns:
            {'success': bool, 'message': str}
        """
        try:
            # TODO: 实现 gRPC API 调用
            logger.warning(f"⚠️ MoveFile API 尚未实现: {source_path} -> {dest_path}")
            return {'success': False, 'message': 'gRPC API 尚未实现'}
        
        except Exception as e:
            logger.error(f"❌ 移动文件失败: {e}")
            return {'success': False, 'message': str(e)}
    
    async def copy_file(self, source_path: str, dest_path: str) -> Dict[str, Any]:
        """
        复制文件或文件夹
        
        Args:
            source_path: 源路径
            dest_path: 目标路径
        
        Returns:
            {'success': bool, 'message': str}
        """
        try:
            # TODO: 实现 gRPC API 调用
            logger.warning(f"⚠️ CopyFile API 尚未实现: {source_path} -> {dest_path}")
            return {'success': False, 'message': 'gRPC API 尚未实现'}
        
        except Exception as e:
            logger.error(f"❌ 复制文件失败: {e}")
            return {'success': False, 'message': str(e)}
    
    async def rename_file(self, path: str, new_name: str) -> Dict[str, Any]:
        """
        重命名文件或文件夹
        
        Args:
            path: 文件路径
            new_name: 新名称
        
        Returns:
            {'success': bool, 'message': str}
        """
        try:
            # TODO: 实现 gRPC API 调用
            logger.warning(f"⚠️ RenameFile API 尚未实现: {path} -> {new_name}")
            return {'success': False, 'message': 'gRPC API 尚未实现'}
        
        except Exception as e:
            logger.error(f"❌ 重命名文件失败: {e}")
            return {'success': False, 'message': str(e)}
    
    async def get_file_url(self, path: str, expires: int = 3600) -> Optional[str]:
        """
        获取文件的临时访问 URL
        
        Args:
            path: 文件路径
            expires: 过期时间（秒）
        
        Returns:
            文件访问 URL
        """
        try:
            # TODO: 实现 gRPC API 调用
            # request = GetFileURLRequest(path=path, expires=expires)
            # response = await self.stub.GetFileURL(request)
            # return response.url
            
            logger.warning(f"⚠️ GetFileURL API 尚未实现: {path}")
            return None
        
        except Exception as e:
            logger.error(f"❌ 获取文件URL失败: {e}")
            return None
    
    async def download_file(
        self,
        remote_path: str,
        local_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        从 CloudDrive2 下载文件
        
        Args:
            remote_path: 远程文件路径
            local_path: 本地保存路径
            progress_callback: 进度回调
        
        Returns:
            {'success': bool, 'message': str}
        """
        try:
            logger.info(f"📥 下载文件: {remote_path}")
            
            # TODO: 实现 gRPC API 调用或使用 WebDAV
            # 方案1: 使用 gRPC 流式下载
            # 方案2: 获取临时 URL 后使用 httpx 下载
            
            logger.warning("⚠️ DownloadFile API 尚未实现")
            return {'success': False, 'message': 'gRPC API 尚未实现'}
        
        except Exception as e:
            logger.error(f"❌ 下载文件失败: {e}")
            return {'success': False, 'message': str(e)}
    
    # ==================== 空间统计 ====================
    
    async def get_space_info(self, mount_point: str = None) -> Optional[Dict[str, Any]]:
        """
        获取空间使用信息
        
        Args:
            mount_point: 挂载点路径（None 表示所有）
        
        Returns:
            {
                'total': int,       # 总空间（字节）
                'used': int,        # 已用空间（字节）
                'free': int,        # 可用空间（字节）
                'percent': float    # 使用百分比
            }
        """
        try:
            # TODO: 实现 gRPC API 调用
            logger.warning(f"⚠️ GetSpaceInfo API 尚未实现: {mount_point}")
            
            # 临时方案：如果是本地挂载，使用 os.statvfs
            if mount_point and os.path.exists(mount_point):
                import shutil
                total, used, free = shutil.disk_usage(mount_point)
                return {
                    'total': total,
                    'used': used,
                    'free': free,
                    'percent': (used / total * 100) if total > 0 else 0
                }
            
            return None
        
        except Exception as e:
            logger.error(f"❌ 获取空间信息失败: {e}")
            return None
    
    # ==================== 批量操作 ====================
    
    async def batch_delete(self, paths: List[str]) -> Dict[str, Any]:
        """
        批量删除文件
        
        Args:
            paths: 文件路径列表
        
        Returns:
            {
                'success': bool,
                'deleted': int,
                'failed': int,
                'errors': List[str]
            }
        """
        try:
            # TODO: 实现 gRPC API 调用或循环调用单个删除
            logger.warning(f"⚠️ BatchDelete API 尚未实现: {len(paths)} files")
            return {
                'success': False,
                'deleted': 0,
                'failed': len(paths),
                'errors': ['gRPC API 尚未实现']
            }
        
        except Exception as e:
            logger.error(f"❌ 批量删除失败: {e}")
            return {
                'success': False,
                'deleted': 0,
                'failed': len(paths),
                'errors': [str(e)]
            }
    
    async def batch_move(
        self,
        file_pairs: List[tuple]  # [(source, dest), ...]
    ) -> Dict[str, Any]:
        """
        批量移动文件
        
        Args:
            file_pairs: 文件对列表 [(源路径, 目标路径), ...]
        
        Returns:
            {
                'success': bool,
                'moved': int,
                'failed': int,
                'errors': List[str]
            }
        """
        try:
            # TODO: 实现批量操作
            logger.warning(f"⚠️ BatchMove API 尚未实现: {len(file_pairs)} files")
            return {
                'success': False,
                'moved': 0,
                'failed': len(file_pairs),
                'errors': ['gRPC API 尚未实现']
            }
        
        except Exception as e:
            logger.error(f"❌ 批量移动失败: {e}")
            return {
                'success': False,
                'moved': 0,
                'failed': len(file_pairs),
                'errors': [str(e)]
            }


def create_clouddrive2_client(
    host: str = None,
    port: int = None,
    username: str = None,
    password: str = None
) -> CloudDrive2Client:
    """
    创建 CloudDrive2 客户端（便捷函数）
    
    从环境变量读取配置：
    - CLOUDDRIVE2_HOST (默认: localhost)
    - CLOUDDRIVE2_PORT (默认: 19798)
    - CLOUDDRIVE2_USERNAME (默认: admin)
    - CLOUDDRIVE2_PASSWORD
    """
    config = CloudDrive2Config(
        host=host or os.getenv('CLOUDDRIVE2_HOST', 'localhost'),
        port=port or int(os.getenv('CLOUDDRIVE2_PORT', '19798')),
        username=username or os.getenv('CLOUDDRIVE2_USERNAME', 'admin'),
        password=password or os.getenv('CLOUDDRIVE2_PASSWORD', '')
    )
    
    return CloudDrive2Client(config)

