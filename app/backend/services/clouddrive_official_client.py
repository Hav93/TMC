"""
CloudDrive2 Official Client

使用官方 proto 生成的 gRPC 客户端
基于: clouddrive.proto (version 0.9.9)
服务: CloudDriveFileSrv
"""
import grpc
from grpc import aio as grpc_aio
import os
import hashlib
from typing import Dict, List, Any, Optional, AsyncIterator
from pathlib import Path

from protos import clouddrive_pb2
from protos import clouddrive_pb2_grpc
from google.protobuf import empty_pb2

from log_manager import get_logger

logger = get_logger(__name__)


class CloudDriveOfficialClient:
    """
    CloudDrive2 官方 gRPC 客户端
    
    使用官方 proto 定义的完整功能
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 19798,
        username: str = "",
        password: str = "",
        use_tls: bool = False
    ):
        """
        初始化客户端
        
        Args:
            host: CloudDrive2 服务器地址
            port: gRPC 端口
            username: 用户名
            password: 密码
            use_tls: 是否使用 TLS
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.address = f"{host}:{port}"
        
        self.channel: Optional[grpc_aio.Channel] = None
        self.stub: Optional[clouddrive_pb2_grpc.CloudDriveFileSrvStub] = None
        self.token: Optional[str] = None
        self.connected = False
    
    async def connect(self) -> bool:
        """
        连接到 CloudDrive2 服务
        
        Returns:
            是否连接成功
        """
        try:
            logger.info(f"🔌 连接到 CloudDrive2: {self.address}")
            
            # 创建 gRPC 通道
            options = [
                ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),
                ('grpc.keepalive_time_ms', 30000),
                ('grpc.keepalive_timeout_ms', 5000),
                ('grpc.keepalive_permit_without_calls', True),
            ]
            
            if self.use_tls:
                credentials = grpc.ssl_channel_credentials()
                self.channel = grpc_aio.secure_channel(
                    self.address,
                    credentials,
                    options=options
                )
            else:
                self.channel = grpc_aio.insecure_channel(
                    self.address,
                    options=options
                )
            
            # 创建 stub
            self.stub = clouddrive_pb2_grpc.CloudDriveFileSrvStub(self.channel)
            logger.info("✅ gRPC Stub 已创建")
            
            # 获取系统信息（测试连接）
            try:
                system_info = await self.get_system_info()
                logger.info(f"✅ CloudDrive 版本: {system_info.cloudDriveVersion}")
                logger.info(f"   用户: {system_info.userName or '未登录'}")
            except Exception as e:
                logger.warning(f"⚠️ 无法获取系统信息: {e}")
            
            # 如果提供了用户名密码，进行认证
            if self.username and self.password:
                await self.authenticate()
            
            self.connected = True
            return True
        
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.channel:
            await self.channel.close()
            self.channel = None
            self.stub = None
            self.connected = False
            logger.info("🔌 已断开连接")
    
    async def authenticate(self) -> bool:
        """
        使用用户名密码获取 JWT token
        
        Returns:
            是否认证成功
        """
        try:
            logger.info(f"🔐 正在认证: {self.username}")
            
            request = clouddrive_pb2.GetTokenRequest(
                userName=self.username,
                password=self.password
            )
            
            response = await self.stub.GetToken(request)
            self.token = response.token
            
            logger.info("✅ 认证成功")
            return True
        
        except Exception as e:
            logger.error(f"❌ 认证失败: {e}")
            return False
    
    def _get_metadata(self) -> List[tuple]:
        """获取请求元数据（包含 token）"""
        if self.token:
            return [('authorization', f'Bearer {self.token}')]
        return []
    
    # ==================== 系统信息 ====================
    
    async def get_system_info(self) -> clouddrive_pb2.CloudDriveSystemInfo:
        """
        获取系统信息
        
        Returns:
            CloudDriveSystemInfo 对象
        """
        try:
            response = await self.stub.GetSystemInfo(empty_pb2.Empty())
            return response
        except Exception as e:
            logger.error(f"❌ 获取系统信息失败: {e}")
            raise
    
    # ==================== 挂载点管理 ====================
    
    async def get_mount_points(self) -> List[clouddrive_pb2.MountPoint]:
        """
        获取所有挂载点
        
        Returns:
            挂载点列表
        """
        try:
            logger.info("📡 调用 gRPC: GetMountPoints")
            
            response = await self.stub.GetMountPoints(
                empty_pb2.Empty(),
                metadata=self._get_metadata()
            )
            
            mount_points = list(response.mountPoints)
            logger.info(f"✅ 找到 {len(mount_points)} 个挂载点")
            
            for mp in mount_points:
                logger.info(f"   - {mp.mountPoint}: {mp.sourceDir} {'(已挂载)' if mp.isMounted else '(未挂载)'}")
            
            return mount_points
        
        except Exception as e:
            logger.error(f"❌ 获取挂载点失败: {e}")
            return []
    
    async def add_mount_point(
        self,
        mount_point: str,
        source_dir: str,
        local_mount: bool = False,
        read_only: bool = False,
        auto_mount: bool = True
    ) -> bool:
        """
        添加挂载点
        
        Args:
            mount_point: 挂载点路径
            source_dir: 源目录
            local_mount: 是否本地挂载
            read_only: 是否只读
            auto_mount: 是否自动挂载
        
        Returns:
            是否成功
        """
        try:
            request = clouddrive_pb2.MountOption(
                mountPoint=mount_point,
                sourceDir=source_dir,
                localMount=local_mount,
                readOnly=read_only,
                autoMount=auto_mount
            )
            
            response = await self.stub.AddMountPoint(
                request,
                metadata=self._get_metadata()
            )
            
            if response.success:
                logger.info(f"✅ 挂载点已添加: {mount_point}")
                return True
            else:
                logger.error(f"❌ 添加挂载点失败: {response.errorMessage}")
                return False
        
        except Exception as e:
            logger.error(f"❌ 添加挂载点异常: {e}")
            return False
    
    # ==================== 文件操作 ====================
    
    async def list_files(
        self,
        path: str,
        refresh: bool = False
    ) -> AsyncIterator[clouddrive_pb2.CloudDriveFile]:
        """
        列出目录下的文件（流式）
        
        Args:
            path: 目录路径
            refresh: 是否刷新缓存
        
        Yields:
            CloudDriveFile 对象
        """
        try:
            logger.info(f"📡 调用 gRPC: GetSubFiles({path})")
            
            request = clouddrive_pb2.ListSubFileRequest(
                path=path,
                refresh=refresh
            )
            
            async for response in self.stub.GetSubFiles(
                request,
                metadata=self._get_metadata()
            ):
                for file in response.files:
                    yield file
        
        except Exception as e:
            logger.error(f"❌ 列出文件失败: {e}")
    
    async def create_folder(
        self,
        path: str,
        folder_name: str
    ) -> bool:
        """
        创建文件夹
        
        Args:
            path: 父目录路径
            folder_name: 文件夹名称
        
        Returns:
            是否成功
        """
        try:
            logger.info(f"📡 调用 gRPC: CreateFolder({path}/{folder_name})")
            
            request = clouddrive_pb2.CreateFolderRequest(
                path=path,
                name=folder_name
            )
            
            response = await self.stub.CreateFolder(
                request,
                metadata=self._get_metadata()
            )
            
            if response.success:
                logger.info(f"✅ 文件夹已创建: {path}/{folder_name}")
                return True
            else:
                logger.error(f"❌ 创建文件夹失败: {response.errorMessage}")
                return False
        
        except Exception as e:
            logger.error(f"❌ 创建文件夹异常: {e}")
            return False
    
    # ==================== 远程上传协议 ====================
    
    async def start_remote_upload(
        self,
        file_path: str,
        file_size: int,
        dest_path: str,
        device_id: str = "TMC"
    ) -> Optional[str]:
        """
        启动远程上传会话
        
        Args:
            file_path: 本地文件路径
            file_size: 文件大小
            dest_path: 目标路径
            device_id: 设备ID
        
        Returns:
            upload_id (会话ID)
        """
        try:
            logger.info(f"📡 调用 gRPC: StartRemoteUpload")
            logger.info(f"   文件: {file_path}")
            logger.info(f"   大小: {file_size} bytes")
            logger.info(f"   目标: {dest_path}")
            
            request = clouddrive_pb2.StartRemoteUploadRequest(
                file_path=dest_path,  # 这是远程路径
                file_size=file_size,
                device_id=device_id
            )
            
            response = await self.stub.StartRemoteUpload(
                request,
                metadata=self._get_metadata()
            )
            
            upload_id = response.upload_id
            logger.info(f"✅ 上传会话已创建: {upload_id}")
            
            return upload_id
        
        except Exception as e:
            logger.error(f"❌ 启动远程上传失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def remote_upload_channel(
        self,
        device_id: str = "TMC"
    ) -> AsyncIterator[clouddrive_pb2.RemoteUploadChannelReply]:
        """
        远程上传通道（服务器流式推送）
        
        Args:
            device_id: 设备ID
        
        Yields:
            RemoteUploadChannelReply 消息
        """
        try:
            request = clouddrive_pb2.RemoteUploadChannelRequest(
                device_id=device_id
            )
            
            async for reply in self.stub.RemoteUploadChannel(
                request,
                metadata=self._get_metadata()
            ):
                yield reply
        
        except Exception as e:
            logger.error(f"❌ 上传通道异常: {e}")
    
    async def send_file_data(
        self,
        upload_id: str,
        offset: int,
        data: bytes
    ) -> bool:
        """
        发送文件数据
        
        Args:
            upload_id: 上传会话ID
            offset: 数据偏移量
            data: 数据内容
        
        Returns:
            是否成功
        """
        try:
            request = clouddrive_pb2.RemoteReadDataUpload(
                upload_id=upload_id,
                offset=offset,
                length=len(data),
                data=data
            )
            
            response = await self.stub.RemoteReadData(
                request,
                metadata=self._get_metadata()
            )
            
            return response.received
        
        except Exception as e:
            logger.error(f"❌ 发送文件数据失败: {e}")
            return False
    
    async def send_hash_progress(
        self,
        upload_id: str,
        bytes_hashed: int,
        total_bytes: int
    ) -> bool:
        """
        发送哈希计算进度
        
        Args:
            upload_id: 上传会话ID
            bytes_hashed: 已哈希字节数
            total_bytes: 总字节数
        
        Returns:
            是否成功
        """
        try:
            request = clouddrive_pb2.RemoteHashProgressUpload(
                upload_id=upload_id,
                bytes_hashed=bytes_hashed,
                total_bytes=total_bytes
            )
            
            await self.stub.RemoteHashProgress(
                request,
                metadata=self._get_metadata()
            )
            
            return True
        
        except Exception as e:
            logger.error(f"❌ 发送哈希进度失败: {e}")
            return False
    
    async def cancel_remote_upload(self, upload_id: str) -> bool:
        """取消远程上传"""
        try:
            request = clouddrive_pb2.RemoteUploadControlRequest(
                upload_id=upload_id,
                cancel=clouddrive_pb2.CancelRemoteUpload()
            )
            
            await self.stub.RemoteUploadControl(
                request,
                metadata=self._get_metadata()
            )
            
            logger.info(f"✅ 上传已取消: {upload_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ 取消上传失败: {e}")
            return False
    
    # ==================== 上下文管理器 ====================
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


# ==================== 工厂函数 ====================

async def create_official_client(
    host: str = None,
    port: int = None,
    username: str = None,
    password: str = None
) -> CloudDriveOfficialClient:
    """
    创建官方 CloudDrive 客户端
    
    Args:
        host: CloudDrive2 主机地址
        port: gRPC 端口
        username: 用户名
        password: 密码
    
    Returns:
        CloudDriveOfficialClient 实例
    """
    host = host or os.getenv('CLOUDDRIVE2_HOST', 'localhost')
    port = port or int(os.getenv('CLOUDDRIVE2_PORT', '19798'))
    username = username or os.getenv('CLOUDDRIVE2_USERNAME', '')
    password = password or os.getenv('CLOUDDRIVE2_PASSWORD', '')
    
    client = CloudDriveOfficialClient(host, port, username, password)
    await client.connect()
    return client

