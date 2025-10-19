"""
CloudDrive2 HTTP Client

当 gRPC protobuf 不可用时，使用 HTTP REST API 作为备选方案
基于官方文档: https://www.clouddrive2.com/api/
"""
import aiohttp
import os
from typing import Dict, List, Any, Optional
from log_manager import get_logger

logger = get_logger(__name__)


class CloudDrive2HTTPClient:
    """
    CloudDrive2 HTTP REST API 客户端
    
    用于在 gRPC 不可用时提供基本功能
    """
    
    def __init__(self, host: str, port: int, username: str = "", password: str = ""):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_url = f"http://{host}:{port}"
        self.session: Optional[aiohttp.ClientSession] = None
        self.token: Optional[str] = None
    
    async def connect(self) -> bool:
        """连接并认证"""
        try:
            self.session = aiohttp.ClientSession()
            
            # 如果有用户名密码，进行认证
            if self.username and self.password:
                auth_url = f"{self.base_url}/api/auth/login"
                async with self.session.post(auth_url, json={
                    "username": self.username,
                    "password": self.password
                }) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.token = data.get('token')
                        logger.info("✅ HTTP API 认证成功")
                    else:
                        logger.warning(f"⚠️ HTTP API 认证失败: {resp.status}")
            
            # 测试连接
            async with self.session.get(f"{self.base_url}/api/fs/list") as resp:
                if resp.status in (200, 401):  # 200 成功，401 需要认证但服务可用
                    logger.info("✅ CloudDrive2 HTTP API 可用")
                    return True
                else:
                    logger.error(f"❌ CloudDrive2 HTTP API 不可用: {resp.status}")
                    return False
        
        except Exception as e:
            logger.error(f"❌ HTTP API 连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {}
        if self.token:
            headers['Authorization'] = f"Bearer {self.token}"
        return headers
    
    async def list_mounts(self) -> List[Dict[str, Any]]:
        """
        列出所有挂载点
        
        Returns:
            [{'name': str, 'path': str, 'cloud_type': str, 'mounted': bool}]
        """
        try:
            if not self.session:
                await self.connect()
            
            # 尝试获取挂载点列表
            # 注意: 实际 API 端点可能不同，需要根据实际文档调整
            async with self.session.get(
                f"{self.base_url}/api/mounts",
                headers=self._get_headers()
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✅ 获取到挂载点列表")
                    return data.get('mounts', [])
                else:
                    logger.warning(f"⚠️ 获取挂载点列表失败: {resp.status}")
                    # 尝试另一个可能的端点
                    return await self._list_mounts_alternative()
        
        except Exception as e:
            logger.error(f"❌ 列出挂载点失败: {e}")
            return []
    
    async def _list_mounts_alternative(self) -> List[Dict[str, Any]]:
        """尝试备选端点"""
        try:
            # 尝试列出根目录，从中推断挂载点
            async with self.session.get(
                f"{self.base_url}/api/fs/list",
                params={'path': '/'},
                headers=self._get_headers()
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    files = data.get('files', [])
                    
                    # 假设根目录下的文件夹就是挂载点
                    mounts = []
                    for file in files:
                        if file.get('type') == 'folder' or file.get('isFolder'):
                            mounts.append({
                                'name': file.get('name', ''),
                                'path': f"/{file.get('name', '')}",
                                'cloud_type': 'unknown',
                                'mounted': True
                            })
                    
                    logger.info(f"✅ 从文件列表推断出 {len(mounts)} 个挂载点")
                    return mounts
        
        except Exception as e:
            logger.debug(f"备选方法也失败: {e}")
        
        return []
    
    async def create_folder(self, path: str) -> bool:
        """创建文件夹"""
        try:
            if not self.session:
                await self.connect()
            
            async with self.session.post(
                f"{self.base_url}/api/fs/mkdir",
                json={'path': path},
                headers=self._get_headers()
            ) as resp:
                if resp.status in (200, 201):
                    logger.info(f"✅ 文件夹创建成功: {path}")
                    return True
                else:
                    logger.warning(f"⚠️ 文件夹创建失败: {resp.status}")
                    return False
        
        except Exception as e:
            logger.error(f"❌ 创建文件夹失败: {e}")
            return False
    
    async def list_files(self, path: str) -> List[Dict[str, Any]]:
        """列出文件"""
        try:
            if not self.session:
                await self.connect()
            
            async with self.session.get(
                f"{self.base_url}/api/fs/list",
                params={'path': path},
                headers=self._get_headers()
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('files', [])
                else:
                    return []
        
        except Exception as e:
            logger.error(f"❌ 列出文件失败: {e}")
            return []


async def create_http_client(
    host: str = None,
    port: int = None,
    username: str = None,
    password: str = None
) -> CloudDrive2HTTPClient:
    """
    创建 HTTP 客户端
    
    Args:
        host: CloudDrive2 主机地址
        port: CloudDrive2 端口
        username: 用户名
        password: 密码
    
    Returns:
        CloudDrive2HTTPClient 实例
    """
    host = host or os.getenv('CLOUDDRIVE2_HOST', 'localhost')
    port = port or int(os.getenv('CLOUDDRIVE2_PORT', '19798'))
    username = username or os.getenv('CLOUDDRIVE2_USERNAME', '')
    password = password or os.getenv('CLOUDDRIVE2_PASSWORD', '')
    
    client = CloudDrive2HTTPClient(host, port, username, password)
    await client.connect()
    return client

