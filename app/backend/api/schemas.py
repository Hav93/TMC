"""
API响应模型定义
提供统一的API响应格式和示例数据
"""
from typing import Any, Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime


class StandardResponse(BaseModel):
    """标准API响应模型"""
    success: bool = Field(description="操作是否成功")
    message: str = Field(description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {"id": 1, "name": "示例"}
            }
        }


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="操作失败")
    message: str = Field(description="错误信息")
    error: Optional[str] = Field(None, description="详细错误信息")
    code: Optional[str] = Field(None, description="错误代码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "操作失败",
                "error": "参数验证失败",
                "code": "VALIDATION_ERROR"
            }
        }


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    success: bool = Field(True, description="操作是否成功")
    message: str = Field("查询成功", description="响应消息")
    data: List[Any] = Field(description="数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "查询成功",
                "data": [
                    {"id": 1, "name": "项目1"},
                    {"id": 2, "name": "项目2"}
                ],
                "total": 100,
                "page": 1,
                "page_size": 20
            }
        }


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名", min_length=3, max_length=50)
    password: str = Field(..., description="密码", min_length=6, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "admin123"
            }
        }


class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool = Field(True, description="登录是否成功")
    message: str = Field("登录成功", description="响应消息")
    token: str = Field(description="JWT访问令牌")
    user: Dict[str, Any] = Field(description="用户信息")
    expires_in: int = Field(description="令牌过期时间（秒）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "登录成功",
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user": {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "is_active": True
                },
                "expires_in": 86400
            }
        }


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(description="服务状态", examples=["healthy", "unhealthy"])
    bot_running: bool = Field(description="Bot是否运行中")
    timestamp: Optional[datetime] = Field(None, description="检查时间")
    version: Optional[str] = Field(None, description="系统版本")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "bot_running": True,
                "timestamp": "2025-01-11T12:00:00",
                "version": "1.3.0"
            }
        }


class ForwardRuleCreate(BaseModel):
    """创建转发规则请求模型"""
    name: str = Field(..., description="规则名称", min_length=1, max_length=100)
    client_id: int = Field(..., description="关联的客户端ID", gt=0)
    source_chats: str = Field(..., description="源聊天ID列表（JSON格式）")
    target_chat_id: Optional[int] = Field(None, description="目标聊天ID")
    enabled: bool = Field(True, description="是否启用")
    keywords: Optional[str] = Field(None, description="关键词列表（JSON格式）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "我的转发规则",
                "client_id": 1,
                "source_chats": "[\"123456789\", \"987654321\"]",
                "target_chat_id": 111222333,
                "enabled": True,
                "keywords": "[\"重要\", \"通知\"]"
            }
        }


class ForwardRuleResponse(BaseModel):
    """转发规则响应模型"""
    id: int = Field(description="规则ID")
    name: str = Field(description="规则名称")
    client_id: int = Field(description="客户端ID")
    enabled: bool = Field(description="是否启用")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "我的转发规则",
                "client_id": 1,
                "enabled": True,
                "created_at": "2025-01-01T10:00:00",
                "updated_at": "2025-01-11T12:00:00"
            }
        }


class MediaMonitorRuleCreate(BaseModel):
    """创建媒体监控规则请求模型"""
    name: str = Field(..., description="规则名称", min_length=1, max_length=100)
    client_id: int = Field(..., description="关联的客户端ID", gt=0)
    source_chats: str = Field(..., description="源聊天ID列表（JSON格式）")
    enabled: bool = Field(True, description="是否启用")
    media_types: Optional[str] = Field(None, description="媒体类型过滤（JSON格式）")
    min_file_size: Optional[int] = Field(None, description="最小文件大小（字节）")
    max_file_size: Optional[int] = Field(None, description="最大文件大小（字节）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "频道视频监控",
                "client_id": 1,
                "source_chats": "[\"123456789\"]",
                "enabled": True,
                "media_types": "[\"video\", \"document\"]",
                "min_file_size": 1048576,
                "max_file_size": 1073741824
            }
        }


class DownloadTaskResponse(BaseModel):
    """下载任务响应模型"""
    id: int = Field(description="任务ID")
    file_name: str = Field(description="文件名")
    file_size: int = Field(description="文件大小（字节）")
    status: str = Field(description="任务状态", examples=["pending", "downloading", "completed", "failed"])
    progress: float = Field(description="下载进度（0-100）")
    created_at: datetime = Field(description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "file_name": "video_2025.mp4",
                "file_size": 52428800,
                "status": "completed",
                "progress": 100.0,
                "created_at": "2025-01-11T10:00:00",
                "completed_at": "2025-01-11T10:05:30"
            }
        }


class TelegramClientCreate(BaseModel):
    """创建Telegram客户端请求模型"""
    name: str = Field(..., description="客户端名称", min_length=1, max_length=100)
    api_id: int = Field(..., description="Telegram API ID", gt=0)
    api_hash: str = Field(..., description="Telegram API Hash", min_length=32, max_length=32)
    phone_number: str = Field(..., description="手机号码（国际格式）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "我的账号",
                "api_id": 12345678,
                "api_hash": "0123456789abcdef0123456789abcdef",
                "phone_number": "+8613800138000"
            }
        }


class TelegramClientResponse(BaseModel):
    """Telegram客户端响应模型"""
    id: int = Field(description="客户端ID")
    name: str = Field(description="客户端名称")
    phone_number: str = Field(description="手机号码")
    is_authorized: bool = Field(description="是否已授权")
    is_active: bool = Field(description="是否激活")
    created_at: datetime = Field(description="创建时间")
    last_active_at: Optional[datetime] = Field(None, description="最后活动时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "我的账号",
                "phone_number": "+8613800138000",
                "is_authorized": True,
                "is_active": True,
                "created_at": "2025-01-01T10:00:00",
                "last_active_at": "2025-01-11T12:00:00"
            }
        }


class Pan115LoginRequest(BaseModel):
    """115网盘登录请求模型"""
    app_id: str = Field(..., description="115开放平台AppID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "app_id": "your_app_id_here"
            }
        }


class Pan115QRCodeResponse(BaseModel):
    """115网盘二维码响应模型"""
    success: bool = Field(True, description="操作是否成功")
    message: str = Field("获取二维码成功", description="响应消息")
    qrcode_url: str = Field(description="二维码图片URL")
    qrcode_token: str = Field(description="二维码令牌（用于查询扫码状态）")
    expires_in: int = Field(description="二维码过期时间（秒）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "获取二维码成功",
                "qrcode_url": "https://qrcodeapi.115.com/api/1.0/web/1.0/qrcode/...",
                "qrcode_token": "abc123def456",
                "expires_in": 300
            }
        }


class SystemStatsResponse(BaseModel):
    """系统统计响应模型"""
    total_rules: int = Field(description="总规则数")
    active_rules: int = Field(description="活跃规则数")
    total_messages: int = Field(description="总消息数")
    total_clients: int = Field(description="总客户端数")
    online_clients: int = Field(description="在线客户端数")
    disk_usage: Dict[str, Any] = Field(description="磁盘使用情况")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_rules": 10,
                "active_rules": 8,
                "total_messages": 15000,
                "total_clients": 3,
                "online_clients": 2,
                "disk_usage": {
                    "total_gb": 500,
                    "used_gb": 120,
                    "free_gb": 380,
                    "usage_percent": 24
                }
            }
        }

