#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天管理API路由

管理Telegram聊天列表
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from log_manager import get_logger
from api.dependencies import get_enhanced_bot
import json

logger = get_logger('api.chats', 'api.log')

router = APIRouter()


@router.get("")
async def list_chats():
    """
    获取所有聊天列表
    
    从所有已连接的Telegram客户端获取聊天列表
    """
    try:
        enhanced_bot = get_enhanced_bot()
        
        # 从增强版机器人获取聊天列表
        if enhanced_bot and enhanced_bot.multi_client_manager:
            all_chats = []
            clients_info = []
            
            for client_id, client_wrapper in enhanced_bot.multi_client_manager.clients.items():
                if client_wrapper.connected:
                    try:
                        # 使用线程安全方法获取聊天列表
                        client_chats = client_wrapper.get_chats_sync()
                        all_chats.extend(client_chats)
                        
                        # 收集客户端信息
                        client_info = {
                            "client_id": client_id,
                            "client_type": client_wrapper.client_type,
                            "chat_count": len(client_chats),
                            "display_name": client_chats[0]["client_display_name"] if client_chats else f"{client_wrapper.client_type}: {client_id}"
                        }
                        clients_info.append(client_info)
                        
                    except Exception as e:
                        logger.warning(f"获取客户端 {client_id} 聊天列表失败: {e}")
                        continue
            
            # 按客户端分组聊天
            chats_by_client = {}
            for chat in all_chats:
                client_id = chat["client_id"]
                if client_id not in chats_by_client:
                    chats_by_client[client_id] = []
                chats_by_client[client_id].append(chat)
            
            return JSONResponse(content={
                "success": True,
                "chats": all_chats,
                "chats_by_client": chats_by_client,
                "clients_info": clients_info,
                "total_chats": len(all_chats),
                "connected_clients": len(clients_info)
            })
        else:
            return JSONResponse(content={
                "success": True,
                "chats": [],
                "chats_by_client": {},
                "clients_info": [],
                "total_chats": 0,
                "connected_clients": 0
            })
    except Exception as e:
        logger.error(f"获取聊天列表失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取聊天列表失败: {str(e)}"
        }, status_code=500)


@router.post("/refresh")
async def refresh_chats():
    """
    刷新聊天列表
    
    在增强模式下，聊天列表是实时的，无需特别刷新
    """
    try:
        return JSONResponse(content={
            "success": True,
            "message": "聊天列表已刷新",
            "updated_count": 0
        })
    except Exception as e:
        logger.error(f"刷新聊天列表失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"刷新聊天列表失败: {str(e)}"
        }, status_code=500)


@router.post("/export")
async def export_chats():
    """
    导出聊天列表为JSON文件
    """
    try:
        enhanced_bot = get_enhanced_bot()
        
        # 从增强版机器人获取聊天列表
        if enhanced_bot and enhanced_bot.multi_client_manager:
            all_chats = []
            
            for client_id, client_wrapper in enhanced_bot.multi_client_manager.clients.items():
                if client_wrapper.connected:
                    try:
                        # 使用线程安全方法获取聊天列表
                        client_chats = client_wrapper.get_chats_sync()
                        all_chats.extend(client_chats)
                    except Exception as e:
                        logger.warning(f"获取客户端 {client_id} 聊天列表失败: {e}")
                        continue
            
            # 返回JSON文件
            json_content = json.dumps(all_chats, indent=2, ensure_ascii=False)
            
            return Response(
                content=json_content,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=chats_export.json"
                }
            )
        else:
            return JSONResponse(content={
                "success": False,
                "message": "没有可用的Telegram客户端"
            }, status_code=400)
    except Exception as e:
        logger.error(f"导出聊天列表失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"导出聊天列表失败: {str(e)}"
        }, status_code=500)


"""
✅ 所有3个端点已完成!

- GET /api/chats - 获取聊天列表
- POST /api/chats/refresh - 刷新聊天列表
- POST /api/chats/export - 导出聊天列表
"""