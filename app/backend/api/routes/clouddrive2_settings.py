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
from pathlib import Path

logger = get_logger('api.clouddrive2_settings')
router = APIRouter()


def save_config_to_file(config_dict: dict):
    """
    将配置保存到 config/app.config 文件
    
    Args:
        config_dict: 要保存的配置字典
    """
    config_file = Path('config/app.config')
    
    # 确保config目录存在
    config_file.parent.mkdir(exist_ok=True)
    
    # 读取现有配置
    existing_config = {}
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_config[key.strip()] = value.strip()
    
    # 更新配置
    existing_config.update(config_dict)
    
    # 写入配置文件
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write("# TMC 配置文件\n")
        f.write("# 此文件由系统自动生成和更新\n\n")
        
        # 分组写入配置
        clouddrive2_keys = [k for k in existing_config.keys() if k.startswith('CLOUDDRIVE2_')]
        other_keys = [k for k in existing_config.keys() if not k.startswith('CLOUDDRIVE2_')]
        
        if clouddrive2_keys:
            f.write("# === CloudDrive2 配置 ===\n")
            for key in sorted(clouddrive2_keys):
                f.write(f"{key}={existing_config[key]}\n")
            f.write("\n")
        
        if other_keys:
            f.write("# === 其他配置 ===\n")
            for key in sorted(other_keys):
                f.write(f"{key}={existing_config[key]}\n")
    
    logger.info(f"✅ 配置已保存到: {config_file}")


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
        # 准备要保存的配置
        config_to_save = {
            'CLOUDDRIVE2_ENABLED': 'true' if data.enabled else 'false',
            'CLOUDDRIVE2_HOST': data.host,
            'CLOUDDRIVE2_PORT': str(data.port),
            'CLOUDDRIVE2_USERNAME': data.username,
            'CLOUDDRIVE2_MOUNT_POINT': data.mount_point,
        }
        
        # 只有提供新密码时才更新
        if data.password and data.password != '***':
            config_to_save['CLOUDDRIVE2_PASSWORD'] = data.password
        else:
            # 保持原有密码
            existing_password = os.getenv('CLOUDDRIVE2_PASSWORD', '')
            if existing_password:
                config_to_save['CLOUDDRIVE2_PASSWORD'] = existing_password
        
        # 保存到配置文件
        save_config_to_file(config_to_save)
        
        # 同时更新运行时环境变量（立即生效）
        for key, value in config_to_save.items():
            os.environ[key] = value
        
        logger.info("✅ CloudDrive2配置已保存并生效")
        
        return {
            "message": "配置保存成功",
            "note": "配置已持久化保存并立即生效"
        }
    except Exception as e:
        logger.error(f"更新CloudDrive2配置失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_clouddrive2_connection(
    data: CloudDrive2ConfigSchema,
    current_user: User = Depends(get_current_user)
):
    """测试CloudDrive2连接"""
    try:
        logger.info(f"🔍 测试CloudDrive2连接: {data.host}:{data.port}")
        
        # 导入CloudDrive2相关类
        from services.clouddrive2_client import CloudDrive2Client, CloudDrive2Config
        
        # 创建配置对象
        config = CloudDrive2Config(
            host=data.host,
            port=data.port,
            username=data.username,
            password=data.password if data.password != '***' else os.getenv('CLOUDDRIVE2_PASSWORD', '')
        )
        
        # 创建临时客户端进行测试
        client = CloudDrive2Client(config)
        
        # 测试连接
        success = await client.connect()
        
        if success:
            # 关闭连接
            await client.disconnect()
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
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"❌ 测试失败: {str(e)}"
        }


class BrowseRequest(BaseModel):
    """目录浏览请求"""
    host: str = "localhost"
    port: int = 19798
    username: str = ""
    password: str = ""
    path: str = "/"


@router.post("/browse")
async def browse_directories(
    data: BrowseRequest,
    current_user: User = Depends(get_current_user)
):
    """浏览 CloudDrive2 目录，仅返回文件夹列表"""
    try:
        from services.clouddrive2_client import CloudDrive2Client, CloudDrive2Config
        # 若未传入，使用环境变量中的当前配置
        host = data.host or os.getenv('CLOUDDRIVE2_HOST', 'localhost')
        port = data.port or int(os.getenv('CLOUDDRIVE2_PORT', '19798'))
        username = data.username or os.getenv('CLOUDDRIVE2_USERNAME', '')
        pwd_env = os.getenv('CLOUDDRIVE2_PASSWORD', '')
        password = (data.password if data.password and data.password != '***' else pwd_env)

        config = CloudDrive2Config(
            host=host,
            port=port,
            username=username,
            password=password
        )

        client = CloudDrive2Client(config)
        await client.connect()
        items = await client.list_files(data.path or "/")
        await client.disconnect()

        # 仅返回目录项
        dirs = [
            {"name": it.get("name"), "path": it.get("path")}
            for it in items if it.get("type") == "folder"
        ]
        return {"success": True, "path": data.path or "/", "items": dirs}

    except Exception as e:
        logger.error(f"❌ 目录浏览失败: {e}")
        return {"success": False, "message": str(e)}

