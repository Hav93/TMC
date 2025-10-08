"""
API路由模块
统一管理所有API路由，与前端API配置保持同步

对应前端: app/frontend/src/services/api-config.ts
"""

from fastapi import APIRouter

# 导入所有路由模块
from . import (
    system,         # 系统管理 - /api/system
    rules,          # 转发规则 - /api/rules
    logs,           # 日志管理 - /api/logs
    chats,          # 聊天管理 - /api/chats
    clients,        # 客户端管理 - /api/clients
    settings,       # 系统设置 - /api/settings
    dashboard,      # 仪表板 - /api/dashboard
    media_monitor,  # 媒体监控 - /api/media/monitor
    media_files,    # 媒体文件 - /api/media
)

# 导出所有路由器
__all__ = [
    'system',
    'rules',
    'logs',
    'chats',
    'clients',
    'settings',
    'dashboard',
    'media_monitor',
    'media_files',
]

# API路由配置信息（用于文档和验证）
API_ROUTE_CONFIG = {
    'system': {
        'prefix': '/api/system',
        'tags': ['系统管理'],
        'router': system.router,
    },
    'rules': {
        'prefix': '/api/rules',
        'tags': ['转发规则'],
        'router': rules.router,
    },
    'logs': {
        'prefix': '/api/logs',
        'tags': ['日志管理'],
        'router': logs.router,
    },
    'chats': {
        'prefix': '/api/chats',
        'tags': ['聊天管理'],
        'router': chats.router,
    },
    'clients': {
        'prefix': '/api/clients',
        'tags': ['客户端管理'],
        'router': clients.router,
    },
    'settings': {
        'prefix': '/api/settings',
        'tags': ['系统设置'],
        'router': settings.router,
    },
    'dashboard': {
        'prefix': '/api/dashboard',
        'tags': ['仪表板'],
        'router': dashboard.router,
    },
    'media_monitor': {
        'prefix': '/api/media/monitor',
        'tags': ['媒体监控'],
        'router': media_monitor.router,
    },
    'media_files': {
        'prefix': '/api/media',
        'tags': ['媒体文件'],
        'router': media_files.router,
    },
}


def register_routes(app):
    """
    注册所有API路由到FastAPI应用
    
    Args:
        app: FastAPI应用实例
    """
    for config in API_ROUTE_CONFIG.values():
        app.include_router(
            config['router'],
            prefix=config['prefix'],
            tags=config['tags']
        )

