"""
CloudDrive2 gRPC Stub Implementation

使用官方 proto 生成的 gRPC 客户端
支持回退到 HTTP API（如果 proto 不可用）

基于官方 API: https://www.clouddrive2.com/api/
"""
import grpc
import os
from grpc import aio as grpc_aio
from typing import Dict, List, Any, Optional
from log_manager import get_logger

logger = get_logger(__name__)

# 尝试导入官方生成的 proto
try:
    from protos import clouddrive_pb2
    from protos import clouddrive_pb2_grpc
    from google.protobuf import empty_pb2
    OFFICIAL_PROTO_AVAILABLE = True
    logger.info("✅ 官方 proto 可用")
except ImportError as e:
    OFFICIAL_PROTO_AVAILABLE = False
    logger.warning(f"⚠️ 官方 proto 不可用，将使用 HTTP 备选方案: {e}")


class CloudDrive2Stub:
    """
    CloudDrive2 gRPC Stub
    
    优先使用官方 proto，回退到 HTTP API
    """
    
    def __init__(self, channel: grpc_aio.Channel):
        self.channel = channel
        self.http_client = None
        self._use_http_fallback = not OFFICIAL_PROTO_AVAILABLE
        
        # 如果官方 proto 可用，创建官方 stub
        if OFFICIAL_PROTO_AVAILABLE:
            self.official_stub = clouddrive_pb2_grpc.CloudDriveFileSrvStub(channel)
            logger.info("✅ 使用官方 gRPC stub")
        else:
            self.official_stub = None
            logger.info("⚠️ 将使用 HTTP API 备选方案")
    
    async def _ensure_http_client(self):
        """确保 HTTP 客户端已初始化"""
        if not self.http_client and self._use_http_fallback:
            try:
                from services.clouddrive2_http_client import create_http_client
                self.http_client = await create_http_client()
                logger.info("✅ HTTP 客户端已初始化（作为 gRPC 备选方案）")
            except Exception as e:
                logger.error(f"❌ HTTP 客户端初始化失败: {e}")
    
    async def ListMounts(self, request: Dict = None) -> List[Dict]:
        """
        列出所有挂载点
        
        Returns:
            List[{
                'name': str,
                'path': str,
                'cloud_type': str,
                'mounted': bool,
                'space_total': int,
                'space_used': int
            }]
        """
        try:
            # 优先使用官方 gRPC
            if self.official_stub:
                logger.info("📡 使用官方 gRPC: GetMountPoints")
                response = await self.official_stub.GetMountPoints(empty_pb2.Empty())
                
                # 转换为字典列表
                mounts = []
                for mp in response.mountPoints:
                    mounts.append({
                        'name': mp.mountPoint,
                        'path': mp.mountPoint,
                        'source_dir': mp.sourceDir,
                        'cloud_type': 'unknown',  # proto 中没有这个字段
                        'mounted': mp.isMounted,
                        'space_total': 0,
                        'space_used': 0
                    })
                
                logger.info(f"✅ 找到 {len(mounts)} 个挂载点")
                return mounts
            
            # 回退到 HTTP API
            if self._use_http_fallback:
                await self._ensure_http_client()
                if self.http_client:
                    logger.info("📡 使用 HTTP API: GET /api/mounts")
                    mounts = await self.http_client.list_mounts()
                    return mounts
            
            logger.warning("⚠️ gRPC 和 HTTP API 都不可用")
            return []
        
        except Exception as e:
            logger.error(f"❌ ListMounts 调用失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def GetMountInfo(self, mount_path: str) -> Optional[Dict]:
        """获取挂载点信息"""
        try:
            logger.warning(f"⚠️ GetMountInfo gRPC 调用尚未实现: {mount_path}")
            return None
        except Exception as e:
            logger.error(f"❌ GetMountInfo 调用失败: {e}")
            return None
    
    async def GetServerInfo(self, request: Dict = None) -> Optional[Dict]:
        """
        获取服务器信息
        
        Returns:
            {
                'version': str,
                'build': str,
                'uptime': int,
                'mounts_count': int
            }
        """
        try:
            logger.warning("⚠️ GetServerInfo gRPC 调用尚未实现")
            return {
                'version': 'unknown',
                'build': 'unknown',
                'uptime': 0,
                'mounts_count': 0
            }
        except Exception as e:
            logger.error(f"❌ GetServerInfo 调用失败: {e}")
            return None
    
    async def CreateUploadSession(
        self,
        file_name: str,
        file_size: int,
        file_hash: str,
        target_path: str,
        cloud_type: str = "115"
    ) -> Optional[Dict]:
        """
        创建上传会话
        
        Returns:
            {
                'success': bool,
                'session_id': str,
                'quick_upload': bool,
                'message': str
            }
        """
        try:
            # 优先使用官方 gRPC: StartRemoteUpload
            if self.official_stub:
                logger.info("📡 使用官方 gRPC: StartRemoteUpload")
                logger.info(f"   文件: {file_name}")
                logger.info(f"   大小: {file_size} bytes")
                logger.info(f"   目标: {target_path}")
                
                request = clouddrive_pb2.StartRemoteUploadRequest(
                    file_path=target_path,  # 目标路径
                    file_size=file_size,
                    device_id="TMC"
                )
                
                response = await self.official_stub.StartRemoteUpload(request)
                
                logger.info(f"✅ 上传会话已创建: {response.upload_id}")
                
                return {
                    'success': True,
                    'session_id': response.upload_id,
                    'quick_upload': False,
                    'message': 'Session created'
                }
            
            # 回退方案
            logger.warning("⚠️ 官方 gRPC 不可用，使用模拟会话")
            import uuid
            return {
                'success': True,
                'session_id': str(uuid.uuid4()),
                'quick_upload': False,
                'message': 'Session created (fallback)'
            }
        except Exception as e:
            logger.error(f"❌ CreateUploadSession 调用失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def UploadChunk(
        self,
        session_id: str,
        chunk_index: int,
        chunk_data: bytes
    ) -> bool:
        """上传数据块"""
        try:
            logger.debug(f"⚠️ UploadChunk gRPC 调用尚未实现: session={session_id[:8]}..., chunk={chunk_index}")
            # 模拟成功
            return True
        except Exception as e:
            logger.error(f"❌ UploadChunk 调用失败: {e}")
            return False
    
    async def CompleteUpload(self, session_id: str) -> Optional[Dict]:
        """
        完成上传
        
        Returns:
            {
                'success': bool,
                'file_id': str,
                'file_path': str,
                'message': str
            }
        """
        try:
            logger.warning(f"⚠️ CompleteUpload gRPC 调用尚未实现: session={session_id[:8]}...")
            return {
                'success': False,
                'file_id': '',
                'file_path': '',
                'message': 'gRPC API not implemented'
            }
        except Exception as e:
            logger.error(f"❌ CompleteUpload 调用失败: {e}")
            return None
    
    async def ListFiles(self, path: str) -> List[Dict]:
        """列出文件"""
        try:
            # 使用 HTTP API 作为备选
            if self._use_http_fallback:
                await self._ensure_http_client()
                if self.http_client:
                    logger.info(f"📡 使用 HTTP API: GET /api/fs/list?path={path}")
                    return await self.http_client.list_files(path)
            
            logger.warning(f"⚠️ ListFiles gRPC 调用尚未实现: {path}")
            return []
        except Exception as e:
            logger.error(f"❌ ListFiles 调用失败: {e}")
            return []
    
    async def CreateFolder(self, path: str) -> bool:
        """创建文件夹"""
        try:
            # 使用 HTTP API 作为备选
            if self._use_http_fallback:
                await self._ensure_http_client()
                if self.http_client:
                    logger.info(f"📡 使用 HTTP API: POST /api/fs/mkdir {path}")
                    return await self.http_client.create_folder(path)
            
            logger.warning(f"⚠️ CreateFolder gRPC 调用尚未实现: {path}")
            return False
        except Exception as e:
            logger.error(f"❌ CreateFolder 调用失败: {e}")
            return False
    
    async def DeleteFile(self, path: str) -> bool:
        """删除文件"""
        try:
            logger.warning(f"⚠️ DeleteFile gRPC 调用尚未实现: {path}")
            return False
        except Exception as e:
            logger.error(f"❌ DeleteFile 调用失败: {e}")
            return False
    
    async def MoveFile(self, source_path: str, dest_path: str) -> bool:
        """移动文件"""
        try:
            logger.warning(f"⚠️ MoveFile gRPC 调用尚未实现: {source_path} -> {dest_path}")
            return False
        except Exception as e:
            logger.error(f"❌ MoveFile 调用失败: {e}")
            return False
    
    async def GetTransferTasks(self, request: Dict = None) -> List[Dict]:
        """获取传输任务"""
        try:
            logger.warning("⚠️ GetTransferTasks gRPC 调用尚未实现")
            return []
        except Exception as e:
            logger.error(f"❌ GetTransferTasks 调用失败: {e}")
            return []
    
    async def ListCloudAPIs(self, request: Dict = None) -> List[Dict]:
        """列出云盘 API"""
        try:
            logger.warning("⚠️ ListCloudAPIs gRPC 调用尚未实现")
            return []
        except Exception as e:
            logger.error(f"❌ ListCloudAPIs 调用失败: {e}")
            return []


def create_stub(channel: grpc_aio.Channel) -> CloudDrive2Stub:
    """
    创建 CloudDrive2 Stub
    
    Args:
        channel: gRPC channel
    
    Returns:
        CloudDrive2Stub 实例
    """
    return CloudDrive2Stub(channel)

