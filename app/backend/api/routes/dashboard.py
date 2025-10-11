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
from sqlalchemy import and_

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


@router.get("/overview")
async def get_dashboard_overview():
    """
    获取仪表板总览数据
    
    包括：
    - 消息转发模块统计
    - 媒体监控模块统计
    - 系统总览
    - 近7日趋势
    """
    try:
        from models import (
            ForwardRule, MessageLog, TelegramClient,
            MediaMonitorRule, DownloadTask, MediaFile
        )
        from database import get_db
        from sqlalchemy import select, func, and_, or_
        from datetime import date
        
        async for db in get_db():
            today = date.today()
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            # ==================== 消息转发模块 ====================
            # 总规则数
            total_forward_rules = await db.scalar(select(func.count(ForwardRule.id))) or 0
            
            # 活跃规则数
            active_forward_rules = await db.scalar(
                select(func.count(ForwardRule.id)).where(ForwardRule.is_active == True)
            ) or 0
            
            # 今日转发消息数
            today_forward_count = await db.scalar(
                select(func.count(MessageLog.id)).where(
                    func.date(MessageLog.created_at) == today
                )
            ) or 0
            
            # 转发成功率
            total_forward_messages = await db.scalar(select(func.count(MessageLog.id))) or 0
            success_forward_messages = await db.scalar(
                select(func.count(MessageLog.id)).where(MessageLog.status == 'success')
            ) or 0
            forward_success_rate = round((success_forward_messages / total_forward_messages * 100), 2) if total_forward_messages > 0 else 100
            
            # 处理中的消息数
            processing_forward = await db.scalar(
                select(func.count(MessageLog.id)).where(MessageLog.status == 'pending')
            ) or 0
            
            # 近7日转发趋势
            forward_trend_query = select(
                func.date(MessageLog.created_at).label('date'),
                func.count(MessageLog.id).label('count')
            ).where(
                MessageLog.created_at >= seven_days_ago
            ).group_by(func.date(MessageLog.created_at)).order_by(func.date(MessageLog.created_at))
            
            forward_trend_result = await db.execute(forward_trend_query)
            forward_trend = [
                {"date": str(row[0]) if row[0] else None, "count": row[1]}
                for row in forward_trend_result.fetchall()
            ]
            
            # ==================== 媒体监控模块 ====================
            # 总监控规则数
            total_monitor_rules = await db.scalar(select(func.count(MediaMonitorRule.id))) or 0
            
            # 活跃监控规则数
            active_monitor_rules = await db.scalar(
                select(func.count(MediaMonitorRule.id)).where(MediaMonitorRule.is_active == True)
            ) or 0
            
            # 今日下载数（成功的任务）
            today_download_count = await db.scalar(
                select(func.count(DownloadTask.id)).where(
                    and_(
                        func.date(DownloadTask.created_at) == today,
                        DownloadTask.status == 'success'
                    )
                )
            ) or 0
            
            # 下载成功率
            total_download_tasks = await db.scalar(select(func.count(DownloadTask.id))) or 0
            success_download_tasks = await db.scalar(
                select(func.count(DownloadTask.id)).where(DownloadTask.status == 'success')
            ) or 0
            download_success_rate = round((success_download_tasks / total_download_tasks * 100), 2) if total_download_tasks > 0 else 100
            
            # 下载中的任务数
            downloading_count = await db.scalar(
                select(func.count(DownloadTask.id)).where(DownloadTask.status == 'downloading')
            ) or 0
            
            # 总存储使用（GB）
            total_storage_mb = await db.scalar(select(func.sum(MediaFile.file_size_mb))) or 0
            total_storage_gb = round(total_storage_mb / 1024, 2)
            
            # 近7日下载趋势
            download_trend_query = select(
                func.date(DownloadTask.created_at).label('date'),
                func.count(DownloadTask.id).label('count')
            ).where(
                and_(
                    DownloadTask.created_at >= seven_days_ago,
                    DownloadTask.status == 'success'
                )
            ).group_by(func.date(DownloadTask.created_at)).order_by(func.date(DownloadTask.created_at))
            
            download_trend_result = await db.execute(download_trend_query)
            download_trend = [
                {"date": str(row[0]) if row[0] else None, "count": row[1]}
                for row in download_trend_result.fetchall()
            ]
            
            # ==================== 文件类型分布 ====================
            file_type_stats = {}
            for file_type in ['video', 'image', 'audio', 'document']:
                count = await db.scalar(
                    select(func.count(MediaFile.id)).where(MediaFile.file_type == file_type)
                ) or 0
                size_mb = await db.scalar(
                    select(func.sum(MediaFile.file_size_mb)).where(MediaFile.file_type == file_type)
                ) or 0
                
                file_type_stats[file_type] = {
                    'count': count,
                    'size_gb': round(size_mb / 1024, 2)
                }
            
            # ==================== 存储分布 ====================
            # 本地存储 - 已归档的文件
            local_organized_count = await db.scalar(
                select(func.count(MediaFile.id)).where(MediaFile.is_organized == True)
            ) or 0
            local_organized_size_mb = await db.scalar(
                select(func.sum(MediaFile.file_size_mb)).where(MediaFile.is_organized == True)
            ) or 0
            
            # 本地存储 - 临时文件（未归档的）
            local_temp_count = await db.scalar(
                select(func.count(MediaFile.id)).where(
                    and_(
                        MediaFile.is_organized == False,
                        MediaFile.temp_path.isnot(None)
                    )
                )
            ) or 0
            local_temp_size_mb = await db.scalar(
                select(func.sum(MediaFile.file_size_mb)).where(
                    and_(
                        MediaFile.is_organized == False,
                        MediaFile.temp_path.isnot(None)
                    )
                )
            ) or 0
            
            # 本地存储总计
            local_count = local_organized_count + local_temp_count
            local_size_mb = local_organized_size_mb + local_temp_size_mb
            
            # 云端存储（115网盘）
            cloud_count = await db.scalar(
                select(func.count(MediaFile.id)).where(MediaFile.is_uploaded_to_cloud == True)
            ) or 0
            cloud_size_mb = await db.scalar(
                select(func.sum(MediaFile.file_size_mb)).where(MediaFile.is_uploaded_to_cloud == True)
            ) or 0
            
            # 115网盘空间信息（从设置中读取）
            from models import MediaSettings
            media_settings_result = await db.execute(select(MediaSettings).limit(1))
            media_settings = media_settings_result.scalar_one_or_none()
            
            pan115_total_space_gb = 0
            pan115_used_space_gb = 0
            pan115_available_space_gb = 0
            
            if media_settings and media_settings.pan115_user_id:
                # 如果有115配置，尝试获取空间信息
                try:
                    from services.p115_service import P115Service
                    p115 = P115Service(cookies=media_settings.pan115_user_key)
                    user_info = await p115.get_user_info(media_settings.pan115_user_key)
                    if user_info:
                        # 转换为GB
                        pan115_total_space_gb = round(user_info.get('space_info', {}).get('all_total', {}).get('size', 0) / (1024**3), 2)
                        pan115_used_space_gb = round((pan115_total_space_gb * user_info.get('space_info', {}).get('all_use', {}).get('size', 0) / 100), 2) if pan115_total_space_gb > 0 else 0
                        pan115_available_space_gb = pan115_total_space_gb - pan115_used_space_gb
                except Exception as e:
                    logger.debug(f"获取115网盘空间信息失败: {e}")
            
            # 收藏文件数
            starred_count = await db.scalar(
                select(func.count(MediaFile.id)).where(MediaFile.is_starred == True)
            ) or 0
            
            # ==================== 系统总览 ====================
            total_rules = total_forward_rules + total_monitor_rules
            active_rules = active_forward_rules + active_monitor_rules
            
            # 系统状态（简单判断）
            system_status = "normal"
            if download_success_rate < 80 or forward_success_rate < 80:
                system_status = "warning"
            if downloading_count > 10 or processing_forward > 50:
                system_status = "busy"
            
            break
        
        return JSONResponse(content={
            "success": True,
            "data": {
                # 系统总览
                "system_overview": {
                    "total_rules": total_rules,
                    "active_rules": active_rules,
                    "today_downloads": today_download_count,
                    "total_storage_gb": total_storage_gb,
                    "system_status": system_status
                },
                
                # 消息转发模块
                "forward_module": {
                    "today_count": today_forward_count,
                    "active_rules": active_forward_rules,
                    "total_rules": total_forward_rules,
                    "success_rate": forward_success_rate,
                    "processing_count": processing_forward,
                    "trend": forward_trend
                },
                
                # 媒体监控模块
                "media_module": {
                    "today_count": today_download_count,
                    "active_rules": active_monitor_rules,
                    "total_rules": total_monitor_rules,
                    "success_rate": download_success_rate,
                    "downloading_count": downloading_count,
                    "storage_gb": total_storage_gb,
                    "trend": download_trend
                },
                
                # 文件类型分布
                "file_type_distribution": file_type_stats,
                
                # 存储分布
                "storage_distribution": {
                    "local": {
                        "organized": {
                            "count": local_organized_count,
                            "size_gb": round(local_organized_size_mb / 1024, 2)
                        },
                        "temp": {
                            "count": local_temp_count,
                            "size_gb": round(local_temp_size_mb / 1024, 2)
                        },
                        "total_count": local_count,
                        "total_size_gb": round(local_size_mb / 1024, 2)
                    },
                    "cloud": {
                        "uploaded": {
                            "count": cloud_count,
                            "size_gb": round(cloud_size_mb / 1024, 2)
                        },
                        "pan115_space": {
                            "total_gb": pan115_total_space_gb,
                            "used_gb": pan115_used_space_gb,
                            "available_gb": pan115_available_space_gb,
                            "usage_percentage": round((pan115_used_space_gb / pan115_total_space_gb * 100), 2) if pan115_total_space_gb > 0 else 0
                        }
                    },
                    "total_gb": total_storage_gb,
                    "cloud_percentage": round((cloud_size_mb / total_storage_mb * 100), 2) if total_storage_mb > 0 else 0
                },
                
                # 其他统计
                "other_stats": {
                    "starred_count": starred_count,
                    "total_files": sum(stats['count'] for stats in file_type_stats.values())
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取仪表板总览失败: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={
            "success": False,
            "message": f"获取仪表板总览失败: {str(e)}"
        }, status_code=500)


@router.get("/insights")
async def get_dashboard_insights():
    """
    获取仪表板智能洞察
    
    包括：
    - 今日高峰时段
    - 最活跃规则
    - 存储预警
    """
    try:
        from models import MediaMonitorRule, DownloadTask, MediaFile
        from database import get_db
        from sqlalchemy import select, func, desc
        from datetime import date
        
        async for db in get_db():
            today = date.today()
            
            # ==================== 今日高峰时段 ====================
            hourly_stats_query = select(
                func.hour(DownloadTask.created_at).label('hour'),
                func.count(DownloadTask.id).label('count')
            ).where(
                and_(
                    func.date(DownloadTask.created_at) == today,
                    DownloadTask.status == 'success'
                )
            ).group_by(func.hour(DownloadTask.created_at)).order_by(desc('count'))
            
            hourly_stats_result = await db.execute(hourly_stats_query)
            peak_hour_row = hourly_stats_result.first()
            
            peak_hour = None
            peak_count = 0
            if peak_hour_row:
                peak_hour = f"{peak_hour_row[0]:02d}:00-{peak_hour_row[0]+1:02d}:00"
                peak_count = peak_hour_row[1]
            
            # ==================== 最活跃规则 ====================
            most_active_query = select(
                MediaMonitorRule.name,
                func.count(DownloadTask.id).label('count')
            ).join(
                DownloadTask, MediaMonitorRule.id == DownloadTask.monitor_rule_id
            ).where(
                and_(
                    func.date(DownloadTask.created_at) == today,
                    DownloadTask.status == 'success'
                )
            ).group_by(MediaMonitorRule.id).order_by(desc('count'))
            
            most_active_result = await db.execute(most_active_query)
            most_active_row = most_active_result.first()
            
            most_active_rule = None
            most_active_count = 0
            if most_active_row:
                most_active_rule = most_active_row[0]
                most_active_count = most_active_row[1]
            
            # ==================== 存储预警 ====================
            # 计算近7日平均增长
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_size_query = select(
                func.sum(MediaFile.file_size_mb)
            ).where(
                MediaFile.downloaded_at >= seven_days_ago
            )
            recent_size_mb = await db.scalar(recent_size_query) or 0
            daily_growth_mb = recent_size_mb / 7 if recent_size_mb > 0 else 0
            
            # 假设存储容量为 500GB（可以从配置读取）
            total_capacity_gb = 500
            current_usage_mb = await db.scalar(select(func.sum(MediaFile.file_size_mb))) or 0
            current_usage_gb = current_usage_mb / 1024
            
            # 计算达到80%需要的天数
            target_capacity_gb = total_capacity_gb * 0.8
            remaining_gb = target_capacity_gb - current_usage_gb
            days_until_80_percent = int(remaining_gb / (daily_growth_mb / 1024)) if daily_growth_mb > 0 else 999
            
            storage_warning = {
                "should_warn": days_until_80_percent < 30,
                "days_until_80_percent": days_until_80_percent if days_until_80_percent > 0 else 0,
                "current_usage_gb": round(current_usage_gb, 2),
                "total_capacity_gb": total_capacity_gb,
                "usage_percentage": round((current_usage_gb / total_capacity_gb * 100), 2)
            }
            
            break
        
        return JSONResponse(content={
            "success": True,
            "insights": {
                "peak_hour": peak_hour,
                "peak_count": peak_count,
                "most_active_rule": most_active_rule,
                "most_active_count": most_active_count,
                "storage_warning": storage_warning
            }
        })
        
    except Exception as e:
        logger.error(f"获取仪表板洞察失败: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={
            "success": False,
            "message": f"获取仪表板洞察失败: {str(e)}"
        }, status_code=500)


"""
✅ 所有3个端点已完成!

- GET /api/dashboard/stats - 获取仪表板统计数据（原有）
- GET /api/dashboard/overview - 获取仪表板总览数据（新增）
- GET /api/dashboard/insights - 获取智能洞察（新增）
"""