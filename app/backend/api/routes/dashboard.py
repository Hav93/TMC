#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪表板API路由

提供系统概览和统计数据
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from log_manager import get_logger
from api.dependencies import get_enhanced_bot
from datetime import datetime, timedelta

logger = get_logger('api.dashboard', 'api.log')

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats():
    """
    获取仪表板统计数据
    
    包括规则数、客户端数、今日消息数、成功率等
    """
    try:
        from models import ForwardRule, MessageLog, TelegramClient
        from database import get_db
        from sqlalchemy import select, func
        from datetime import date
        
        stats = {}
        
        async for db in get_db():
            # 规则统计
            total_rules_result = await db.execute(select(func.count(ForwardRule.id)))
            total_rules = total_rules_result.scalar() or 0
            
            active_rules_result = await db.execute(
                select(func.count(ForwardRule.id)).where(ForwardRule.is_active == True)
            )
            active_rules = active_rules_result.scalar() or 0
            
            # 客户端统计
            total_clients_result = await db.execute(select(func.count(TelegramClient.id)))
            total_clients = total_clients_result.scalar() or 0
            
            # 获取运行中的客户端数
            enhanced_bot = get_enhanced_bot()
            running_clients = 0
            connected_clients = 0
            if enhanced_bot and hasattr(enhanced_bot, 'get_client_status'):
                clients_status = enhanced_bot.get_client_status()
                running_clients = sum(1 for client in clients_status.values() if client.get("running", False))
                connected_clients = sum(1 for client in clients_status.values() if client.get("connected", False))
            
            # 消息日志统计
            total_messages_result = await db.execute(select(func.count(MessageLog.id)))
            total_messages = total_messages_result.scalar() or 0
            
            # 今日消息数
            today = date.today()
            today_messages_result = await db.execute(
                select(func.count(MessageLog.id)).where(
                    func.date(MessageLog.created_at) == today
                )
            )
            today_messages = today_messages_result.scalar() or 0
            
            # 成功消息数
            success_messages_result = await db.execute(
                select(func.count(MessageLog.id)).where(MessageLog.status == 'success')
            )
            success_messages = success_messages_result.scalar() or 0
            
            # 失败消息数
            failed_messages_result = await db.execute(
                select(func.count(MessageLog.id)).where(MessageLog.status == 'failed')
            )
            failed_messages = failed_messages_result.scalar() or 0
            
            # 计算成功率
            success_rate = 0
            if total_messages > 0:
                success_rate = round((success_messages / total_messages) * 100, 2)
            
            # 最近7天的消息统计
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_messages_query = select(
                func.date(MessageLog.created_at).label('date'),
                func.count(MessageLog.id).label('count')
            ).where(
                MessageLog.created_at >= seven_days_ago
            ).group_by(func.date(MessageLog.created_at)).order_by(func.date(MessageLog.created_at))
            
            recent_messages_result = await db.execute(recent_messages_query)
            recent_messages_data = [
                {
                    "date": row[0].isoformat() if row[0] else None,
                    "count": row[1]
                }
                for row in recent_messages_result.fetchall()
            ]
            
            stats = {
                "rules": {
                    "total": total_rules,
                    "active": active_rules,
                    "inactive": total_rules - active_rules
                },
                "clients": {
                    "total": total_clients,
                    "running": running_clients,
                    "connected": connected_clients
                },
                "messages": {
                    "total": total_messages,
                    "today": today_messages,
                    "success": success_messages,
                    "failed": failed_messages,
                    "success_rate": success_rate
                },
                "recent_activity": recent_messages_data
            }
            
            break
        
        return JSONResponse(content={
            "success": True,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"获取仪表板统计失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取仪表板统计失败: {str(e)}"
        }, status_code=500)


"""
✅ 所有1个端点已完成!

- GET /api/dashboard/stats - 获取仪表板统计数据
"""