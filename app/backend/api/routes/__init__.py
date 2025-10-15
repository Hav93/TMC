"""
API路由模块
统一管理所有API路由，与前端API配置保持同步

对应前端: app/frontend/src/services/api-config.ts
"""

from fastapi import APIRouter

# 导入所有路由模块
from . import (
    system,          # 系统管理 - /api/system
    rules,           # 转发规则 - /api/rules
    logs,            # 日志管理 - /api/logs
    chats,           # 聊天管理 - /api/chats
    clients,         # 客户端管理 - /api/clients
    settings,        # 系统设置 - /api/settings
    dashboard,       # 仪表板 - /api/dashboard
    media_monitor,   # 媒体监控 - /api/media/monitor
    media_files,     # 媒体文件 - /api/media
    media_settings,  # 媒体配置 - /api/settings/media
    pan115,          # 115网盘 - /api/pan115
    resource_monitor,# 资源监控 - /api/resources
    performance,     # 性能监控 - /api/performance
    notifications,   # 通知系统 - /api/notifications
    ad_filter,       # 广告过滤 - /api/ad-filter
    quick_upload,    # 秒传检测 - /api/quick-upload
    smart_rename,    # 智能重命名 - /api/smart-rename
    strm,            # STRM生成 - /api/strm
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
    'media_settings',
    'pan115',
    'resource_monitor',
    'performance',
    'notifications',
    'ad_filter',
    'quick_upload',
    'smart_rename',
    'strm',
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
    'media_settings': {
        'prefix': '/api/settings/media',
        'tags': ['媒体配置'],
        'router': media_settings.router,
    },
    'pan115': {
        'prefix': '/api/pan115',
        'tags': ['115网盘'],
        'router': pan115.router,
    },
    'resource_monitor': {
        'prefix': '/api/resources',
        'tags': ['资源监控'],
        'router': resource_monitor.router,
    },
    'performance': {
        'prefix': '/api/performance',
        'tags': ['性能监控'],
        'router': performance.router,
    },
    'notifications': {
        'prefix': '/api/notifications',
        'tags': ['通知系统'],
        'router': notifications.router,
    },
    'ad_filter': {
        'prefix': '/api/ad-filter',
        'tags': ['广告过滤'],
        'router': ad_filter.router,
    },
    'quick_upload': {
        'prefix': '/api/quick-upload',
        'tags': ['秒传检测'],
        'router': quick_upload.router,
    },
    'smart_rename': {
        'prefix': '/api/smart-rename',
        'tags': ['智能重命名'],
        'router': smart_rename.router,
    },
    'strm': {
        'prefix': '/api/strm',
        'tags': ['STRM生成'],
        'router': strm.router,
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

