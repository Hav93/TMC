#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统设置API路由

管理系统配置
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from log_manager import get_logger

logger = get_logger('api.settings', 'api.log')

router = APIRouter()


@router.get("")
async def get_settings():
    """
    获取系统设置
    
    返回当前的系统配置
    """
    try:
        logger.info("📋 获取系统设置")
        from config import Config
        
        # 返回当前配置
        settings = {
            "api_id": getattr(Config, 'API_ID', ''),
            "api_hash": getattr(Config, 'API_HASH', ''),
            "bot_token": getattr(Config, 'BOT_TOKEN', ''),
            "phone_number": getattr(Config, 'PHONE_NUMBER', ''),
            "admin_user_ids": getattr(Config, 'ADMIN_USER_IDS', ''),
            "enable_proxy": getattr(Config, 'ENABLE_PROXY', False),
            "proxy_type": getattr(Config, 'PROXY_TYPE', 'http'),
            "proxy_host": getattr(Config, 'PROXY_HOST', '127.0.0.1'),
            "proxy_port": getattr(Config, 'PROXY_PORT', '7890'),
            "proxy_username": getattr(Config, 'PROXY_USERNAME', ''),
            "proxy_password": "***" if getattr(Config, 'PROXY_PASSWORD', '') else '',
            "enable_log_cleanup": getattr(Config, 'ENABLE_LOG_CLEANUP', False),
            "log_retention_days": getattr(Config, 'LOG_RETENTION_DAYS', '30'),
            "log_cleanup_time": getattr(Config, 'LOG_CLEANUP_TIME', '02:00'),
            "max_log_size": getattr(Config, 'MAX_LOG_SIZE', '100'),
        }
        
        logger.info("✅ 系统设置获取成功")
        return JSONResponse(content={
            "success": True,
            "config": settings
        })
    except Exception as e:
        logger.error(f"❌ 获取设置失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取设置失败: {str(e)}"
        }, status_code=500)


@router.post("")
async def save_settings(request: Request):
    """
    保存系统设置
    
    更新 config/app.config 文件并重新加载配置
    """
    try:
        data = await request.json()
        logger.info("💾 开始保存系统设置...")
        
        # 记录主要配置项的变更
        config_changes = []
        if data.get('api_id'):
            config_changes.append(f"API_ID: {'已设置' if data.get('api_id') else '未设置'}")
        if data.get('phone_number'):
            config_changes.append(f"Phone: {data.get('phone_number')}")
        if data.get('enable_proxy'):
            proxy_info = f"{data.get('proxy_type', 'http')}://{data.get('proxy_host', '127.0.0.1')}:{data.get('proxy_port', '7890')}"
            config_changes.append(f"代理: {proxy_info}")
        else:
            config_changes.append("代理: 已禁用")
        
        logger.info(f"📝 配置变更: {', '.join(config_changes)}")
        
        # 构建新的配置内容
        config_lines = []
        
        # Telegram配置
        config_lines.append("# Telegram API配置")
        config_lines.append(f"API_ID={data.get('api_id', '')}")
        config_lines.append(f"API_HASH={data.get('api_hash', '')}")
        config_lines.append(f"BOT_TOKEN={data.get('bot_token', '')}")
        config_lines.append(f"PHONE_NUMBER={data.get('phone_number', '')}")
        config_lines.append(f"ADMIN_USER_IDS={data.get('admin_user_ids', '')}")
        config_lines.append("")
        
        # 代理配置
        config_lines.append("# 代理配置")
        enable_proxy = data.get('enable_proxy', False)
        config_lines.append(f"ENABLE_PROXY={str(enable_proxy).lower()}")
        
        # 只有在启用代理时才写入代理参数
        if enable_proxy:
            config_lines.append(f"PROXY_TYPE={data.get('proxy_type', 'http')}")
            config_lines.append(f"PROXY_HOST={data.get('proxy_host', '127.0.0.1')}")
            config_lines.append(f"PROXY_PORT={data.get('proxy_port', '7890')}")
            config_lines.append(f"PROXY_USERNAME={data.get('proxy_username', '')}")
            if data.get('proxy_password') and data.get('proxy_password') != '***':
                config_lines.append(f"PROXY_PASSWORD={data.get('proxy_password', '')}")
            logger.info(f"🌐 代理配置已启用: {data.get('proxy_type', 'http')}://{data.get('proxy_host', '127.0.0.1')}:{data.get('proxy_port', '7890')}")
        else:
            config_lines.append("# PROXY_TYPE=http")
            config_lines.append("# PROXY_HOST=127.0.0.1") 
            config_lines.append("# PROXY_PORT=7890")
            config_lines.append("# PROXY_USERNAME=")
            config_lines.append("# PROXY_PASSWORD=")
            logger.info("🚫 代理配置已禁用")
        
        config_lines.append("")
        
        # 日志配置
        config_lines.append("# 日志管理配置")
        config_lines.append(f"ENABLE_LOG_CLEANUP={str(data.get('enable_log_cleanup', False)).lower()}")
        config_lines.append(f"LOG_RETENTION_DAYS={data.get('log_retention_days', '30')}")
        config_lines.append(f"LOG_CLEANUP_TIME={data.get('log_cleanup_time', '02:00')}")
        config_lines.append(f"MAX_LOG_SIZE={data.get('max_log_size', '100')}")
        config_lines.append("")
        
        logger.info(f"📊 日志清理: {'启用' if data.get('enable_log_cleanup') else '禁用'}, 保留天数: {data.get('log_retention_days', '30')}天")
        
        # 写入配置文件（优先使用 config/app.config）
        import os
        from pathlib import Path
        
        config_content = "\n".join(config_lines)
        
        # 确保配置目录存在
        config_dir = Path('config')
        config_dir.mkdir(exist_ok=True)
        
        # 写入到 config/app.config（持久化配置文件）
        config_file = config_dir / 'app.config'
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        logger.info(f"💾 配置已保存到: {config_file}")
        
        # 重新加载配置
        from config import Config
        Config.reload()
        
        # 重新加载代理管理器（重要！确保代理配置立即生效）
        from proxy_utils import reload_proxy_manager
        reload_proxy_manager()
        
        logger.info("🔄 配置重新加载完成（包括代理管理器）")
        logger.info("✅ 系统配置保存成功！代理配置已生效，新启动的客户端将使用新配置")
        
        # 检查是否有代理配置变更
        proxy_changed = enable_proxy or data.get('proxy_host') or data.get('proxy_port')
        
        return JSONResponse(content={
            "success": True,
            "message": "设置保存成功！代理配置已更新，请重启已运行的客户端以使其生效。" if proxy_changed else "设置保存成功！",
            "requires_client_restart": proxy_changed
        })
    except Exception as e:
        logger.error(f"❌ 保存设置失败: {e}", exc_info=True)
        return JSONResponse(content={
            "success": False,
            "message": f"保存设置失败: {str(e)}"
        }, status_code=500)


"""
✅ 所有2个端点已完成!

- GET /api/settings - 获取系统设置
- POST /api/settings - 保存系统设置
"""