"""
CloudDrive2 配置 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from models import User
from auth import get_current_user
from log_manager import get_logger
import os
from services.clouddrive2_client import CloudDrive2Client

logger = get_logger('api.clouddrive2_settings')
router = APIRouter()


class CloudDrive2ConfigSchema(BaseModel):
    """CloudDrive2配置Schema"""
    enabled: bool = False
    host: str = "localhost"
    port: int = 19798
    username: str = ""
    password: str = ""
    mount_point: str = "/CloudNAS/115"


@router.get("/")
async def get_clouddrive2_config(
    current_user: User = Depends(get_current_user)
):
    """获取CloudDrive2配置"""
    try:
        # 从环境变量读取配置
        config = {
            "enabled": os.getenv('CLOUDDRIVE2_ENABLED', 'false').lower() == 'true',
            "host": os.getenv('CLOUDDRIVE2_HOST', 'localhost'),
            "port": int(os.getenv('CLOUDDRIVE2_PORT', '19798')),
            "username": os.getenv('CLOUDDRIVE2_USERNAME', ''),
            "password": '***' if os.getenv('CLOUDDRIVE2_PASSWORD') else '',
            "mount_point": os.getenv('CLOUDDRIVE2_MOUNT_POINT', '/CloudNAS/115'),
        }
        
        logger.info("📝 获取CloudDrive2配置")
        return config
    except Exception as e:
        logger.error(f"获取CloudDrive2配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/")
async def update_clouddrive2_config(
    data: CloudDrive2ConfigSchema,
    current_user: User = Depends(get_current_user)
):
    """更新CloudDrive2配置"""
    try:
        # 更新环境变量
        os.environ['CLOUDDRIVE2_ENABLED'] = 'true' if data.enabled else 'false'
        os.environ['CLOUDDRIVE2_HOST'] = data.host
        os.environ['CLOUDDRIVE2_PORT'] = str(data.port)
        os.environ['CLOUDDRIVE2_USERNAME'] = data.username
        
        # 只有提供新密码时才更新
        if data.password and data.password != '***':
            os.environ['CLOUDDRIVE2_PASSWORD'] = data.password
        
        os.environ['CLOUDDRIVE2_MOUNT_POINT'] = data.mount_point
        
        logger.info("✅ CloudDrive2配置已更新")
        
        return {
            "message": "配置更新成功",
            "note": "环境变量已更新，重启后生效"
        }
    except Exception as e:
        logger.error(f"更新CloudDrive2配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_clouddrive2_connection(
    data: CloudDrive2ConfigSchema,
    current_user: User = Depends(get_current_user)
):
    """测试CloudDrive2连接"""
    try:
        logger.info(f"🔍 测试CloudDrive2连接: {data.host}:{data.port}")
        
        # 创建临时客户端进行测试
        client = CloudDrive2Client(
            host=data.host,
            port=data.port,
            username=data.username,
            password=data.password if data.password != '***' else os.getenv('CLOUDDRIVE2_PASSWORD', '')
        )
        
        # 测试连接
        success = await client.test_connection()
        
        if success:
            logger.info("✅ CloudDrive2连接测试成功")
            return {
                "success": True,
                "message": "✅ CloudDrive2连接测试成功！\n服务正常运行"
            }
        else:
            logger.warning("❌ CloudDrive2连接测试失败")
            return {
                "success": False,
                "message": "❌ CloudDrive2连接失败\n请检查服务是否运行及配置是否正确"
            }
    except ImportError as e:
        logger.error(f"❌ CloudDrive2模块导入失败: {e}")
        return {
            "success": False,
            "message": "❌ CloudDrive2模块未安装\n请先安装 grpcio 和 grpcio-tools:\npip install grpcio grpcio-tools"
        }
    except Exception as e:
        logger.error(f"❌ CloudDrive2连接测试异常: {e}")
        return {
            "success": False,
            "message": f"❌ 测试失败: {str(e)}"
        }

