#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息日志API路由

管理消息转发日志
"""

from fastapi import APIRouter, Query, Request, Body, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime
from typing import Optional, Dict, Any, List
from log_manager import get_logger
from sqlalchemy import select, desc, and_, func
from auth import get_current_user
from models import User
import json
import io

logger = get_logger('api.logs', 'api.log')

router = APIRouter()


@router.get("")
async def list_logs(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(50, ge=1, le=5000, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    rule_id: Optional[int] = Query(None, description="规则ID筛选"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)")
):
    """
    获取消息日志列表
    
    支持分页、筛选、日期范围查询
    """
    try:
        from models import MessageLog
        from database import get_db
        from sqlalchemy.orm import joinedload
        
        async for db in get_db():
            # 构建查询
            query = select(MessageLog)
            
            # 状态筛选
            if status:
                query = query.where(MessageLog.status == status)
            
            # 规则ID筛选
            if rule_id:
                query = query.where(MessageLog.rule_id == rule_id)
            
            # 日期范围筛选
            if start_date or end_date:
                date_conditions = []
                if start_date:
                    try:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                        date_conditions.append(func.date(MessageLog.created_at) >= start_dt)
                    except ValueError:
                        logger.warning(f"无效的开始日期格式: {start_date}")
                
                if end_date:
                    try:
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                        date_conditions.append(func.date(MessageLog.created_at) <= end_dt)
                    except ValueError:
                        logger.warning(f"无效的结束日期格式: {end_date}")
                
                if date_conditions:
                    query = query.where(and_(*date_conditions))
            
            # 排序（最新的在前）
            query = query.order_by(desc(MessageLog.created_at))
            
            # 分页
            offset = (page - 1) * limit
            paginated_query = query.offset(offset).limit(limit)
            
            # 执行查询，预加载规则信息
            paginated_query = paginated_query.options(joinedload(MessageLog.rule))
            result = await db.execute(paginated_query)
            logs = result.scalars().all()
            
            # 获取总数（应用相同的筛选条件）
            count_query = select(MessageLog)
            if status:
                count_query = count_query.where(MessageLog.status == status)
            if rule_id:
                count_query = count_query.where(MessageLog.rule_id == rule_id)
            
            # 日期范围筛选（重要：总数也要应用日期过滤）
            if start_date or end_date:
                date_conditions = []
                if start_date:
                    try:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                        date_conditions.append(func.date(MessageLog.created_at) >= start_dt)
                    except ValueError:
                        pass
                
                if end_date:
                    try:
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                        date_conditions.append(func.date(MessageLog.created_at) <= end_dt)
                    except ValueError:
                        pass
                
                if date_conditions:
                    count_query = count_query.where(and_(*date_conditions))
            count_result = await db.execute(count_query)
            total = len(count_result.scalars().all())
            
            # 调试日志
            logger.info(f"📊 日志查询: page={page}, limit={limit}, status={status}, rule_id={rule_id}, start_date={start_date}, end_date={end_date}")
            logger.info(f"📊 查询结果: 返回 {len(logs)} 条, 总计 {total} 条")
            
            # 序列化日志数据
            logs_data = []
            for log in logs:
                # 获取规则名称（通过预加载的关系）
                rule_name = None
                if log.rule and hasattr(log.rule, 'name'):
                    rule_name = log.rule.name
                elif log.rule_id:
                    rule_name = f"规则 #{log.rule_id}"
                
                log_data = {
                    "id": log.id,
                    "rule_id": log.rule_id,
                    "rule_name": rule_name,
                    # 前端期望的字段名映射
                    "message_id": log.source_message_id,
                    "forwarded_message_id": log.target_message_id,
                    "source_chat_id": log.source_chat_id,
                    "source_chat_name": log.source_chat_name,
                    "target_chat_id": log.target_chat_id,
                    "target_chat_name": log.target_chat_name,
                    "message_text": log.original_text,
                    "message_type": log.media_type or 'text',
                    "status": log.status,
                    "error_message": log.error_message,
                    "processing_time": log.processing_time,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                logs_data.append(log_data)
            
            return JSONResponse(content={
                "success": True,
                "items": logs_data,  # 前端期望 items 字段
                "total": total,
                "page": page,
                "limit": limit
            })
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取日志失败: {str(e)}"
        }, status_code=500)


@router.get("/stats")
async def get_log_stats():
    """
    获取日志统计信息
    
    返回各状态的日志数量、今日转发数等
    """
    try:
        from models import MessageLog
        from database import get_db
        from sqlalchemy import func
        from datetime import date
        
        async for db in get_db():
            # 按状态统计
            status_stats_query = select(
                MessageLog.status,
                func.count(MessageLog.id).label('count')
            ).group_by(MessageLog.status)
            status_result = await db.execute(status_stats_query)
            status_stats = {row[0]: row[1] for row in status_result.fetchall()}
            
            # 今日统计
            today = date.today()
            today_query = select(func.count(MessageLog.id)).where(
                func.date(MessageLog.created_at) == today
            )
            today_result = await db.execute(today_query)
            today_count = today_result.scalar() or 0
            
            # 总计
            total_query = select(func.count(MessageLog.id))
            total_result = await db.execute(total_query)
            total_count = total_result.scalar() or 0
            
            return JSONResponse(content={
                "success": True,
                "stats": {
                    "total": total_count,
                    "today": today_count,
                    "by_status": status_stats
                }
            })
    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取日志统计失败: {str(e)}"
        }, status_code=500)


@router.delete("/{log_id}")
async def delete_log(log_id: int):
    """
    删除单条日志
    """
    try:
        from models import MessageLog
        from database import get_db
        from sqlalchemy import delete
        
        logger.info(f"🗑️ 请求删除日志: ID={log_id}")
        
        async for db in get_db():
            result = await db.execute(
                delete(MessageLog).where(MessageLog.id == log_id)
            )
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"✅ 日志删除成功: ID={log_id}")
                return JSONResponse({
                    "success": True,
                    "message": "日志删除成功"
                })
            else:
                logger.warning(f"⚠️ 日志不存在: ID={log_id}")
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "message": "日志不存在"}
                )
    except Exception as e:
        logger.error(f"❌ 删除日志失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"删除日志失败: {str(e)}"}
        )


@router.post("/batch-delete")
async def batch_delete_logs(request: Request):
    """
    批量删除日志
    """
    try:
        from models import MessageLog
        from database import get_db
        from sqlalchemy import delete
        
        body = await request.json()
        ids = body.get('ids', [])
        
        logger.info(f"🗑️ 请求批量删除日志: IDs={ids}, 共 {len(ids)} 条")
        
        if not ids:
            logger.warning("⚠️ 批量删除请求中没有提供ID列表")
            return JSONResponse({
                "success": False,
                "message": "请提供要删除的日志ID列表"
            }, status_code=400)
        
        async for db in get_db():
            result = await db.execute(
                delete(MessageLog).where(MessageLog.id.in_(ids))
            )
            await db.commit()
            
            logger.info(f"✅ 批量删除日志成功: 请求删除 {len(ids)} 条，实际删除 {result.rowcount} 条")
            return JSONResponse({
                "success": True,
                "message": f"成功删除 {result.rowcount} 条日志"
            })
    except Exception as e:
        logger.error(f"❌ 批量删除日志失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"批量删除日志失败: {str(e)}"}
        )


@router.post("/export")
async def export_logs(
    filters: Optional[Dict[str, Any]] = Body(default={}),
    current_user: User = Depends(get_current_user)
):
    """
    导出日志为JSON文件
    
    支持与list_logs相同的筛选参数
    需要登录认证
    """
    try:
        from models import MessageLog
        from database import get_db
        
        async for db in get_db():
            # 构建查询（与list_logs类似，但不分页）
            query = select(MessageLog).order_by(desc(MessageLog.created_at))
            
            # 应用筛选
            conditions = []
            
            if filters.get('status'):
                conditions.append(MessageLog.status == filters['status'])
            
            if filters.get('rule_id'):
                conditions.append(MessageLog.rule_id == filters['rule_id'])
            
            if filters.get('start_date'):
                try:
                    start_dt = datetime.strptime(filters['start_date'], '%Y-%m-%d')
                    conditions.append(MessageLog.created_at >= start_dt)
                except ValueError:
                    pass
            
            if filters.get('end_date'):
                try:
                    # 结束日期包含当天全天
                    end_dt = datetime.strptime(filters['end_date'], '%Y-%m-%d')
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                    conditions.append(MessageLog.created_at <= end_dt)
                except ValueError:
                    pass
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # 执行查询
            result = await db.execute(query)
            logs = result.scalars().all()
            
            # 转换为JSON格式
            logs_data = []
            for log in logs:
                logs_data.append({
                    'id': log.id,
                    'rule_id': log.rule_id,
                    'rule_name': log.rule_name,
                    'source_chat_id': log.source_chat_id,
                    'source_chat_name': log.source_chat_name,
                    'source_message_id': log.source_message_id,
                    'target_chat_id': log.target_chat_id,
                    'target_chat_name': log.target_chat_name,
                    'target_message_id': log.target_message_id,
                    'original_text': log.original_text,
                    'processed_text': log.processed_text,
                    'media_type': log.media_type,
                    'status': log.status,
                    'error_message': log.error_message,
                    'processing_time': log.processing_time,
                    'content_hash': log.content_hash,
                    'media_hash': log.media_hash,
                    'sender_id': log.sender_id,
                    'sender_username': log.sender_username,
                    'created_at': log.created_at.isoformat() if log.created_at else None,
                })
            
            # 生成JSON文件
            json_str = json.dumps(logs_data, ensure_ascii=False, indent=2)
            json_bytes = json_str.encode('utf-8')
            
            logger.info(f"导出日志成功: {len(logs_data)} 条记录")
            
            # 返回文件流
            return StreamingResponse(
                io.BytesIO(json_bytes),
                media_type='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename="logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
                }
            )
    except Exception as e:
        logger.error(f"导出日志失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"导出日志失败: {str(e)}"}
        )


@router.post("/import")
async def import_logs(
    data: List[Dict[str, Any]] = Body(..., embed=True),
    current_user: User = Depends(get_current_user)
):
    """
    导入日志记录
    
    从JSON格式导入日志，支持批量导入
    需要登录认证
    """
    try:
        from models import MessageLog
        from database import get_db
        
        if not data:
            return JSONResponse({
                "success": False,
                "message": "导入数据为空"
            })
        
        async for db in get_db():
            imported_count = 0
            
            for log_data in data:
                try:
                    # 创建日志记录（使用正确的字段名）
                    new_log = MessageLog(
                        rule_id=log_data.get("rule_id"),
                        rule_name=log_data.get("rule_name"),
                        source_chat_id=log_data.get("source_chat_id", ""),
                        source_chat_name=log_data.get("source_chat_name"),
                        source_message_id=log_data.get("source_message_id", 0),
                        target_chat_id=log_data.get("target_chat_id", ""),
                        target_chat_name=log_data.get("target_chat_name"),
                        target_message_id=log_data.get("target_message_id"),
                        original_text=log_data.get("original_text"),
                        processed_text=log_data.get("processed_text"),
                        media_type=log_data.get("media_type"),
                        status=log_data.get("status", "success"),
                        error_message=log_data.get("error_message"),
                        processing_time=log_data.get("processing_time"),
                        content_hash=log_data.get("content_hash"),
                        media_hash=log_data.get("media_hash"),
                        sender_id=log_data.get("sender_id"),
                        sender_username=log_data.get("sender_username"),
                    )
                    
                    # 处理时间字段
                    if log_data.get("created_at"):
                        from datetime import datetime
                        new_log.created_at = datetime.fromisoformat(log_data["created_at"])
                    
                    db.add(new_log)
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"导入日志失败 (跳过): {log_data.get('id', 'Unknown')} - {e}")
                    continue
            
            await db.commit()
            
            logger.info(f"导入日志成功: {imported_count}/{len(data)} 条")
            
            return JSONResponse({
                "success": True,
                "imported_count": imported_count,
                "message": f"成功导入 {imported_count} 条日志（总共 {len(data)} 条）"
            })
            
    except Exception as e:
        logger.error(f"导入日志失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"导入日志失败: {str(e)}"}
        )


"""
✅ 所有日志端点已完成!

- GET /api/logs - 获取日志列表 (支持分页、筛选、日期范围)
- GET /api/logs/stats - 获取日志统计
- DELETE /api/logs/{log_id} - 删除单条日志
- POST /api/logs/batch-delete - 批量删除日志
- POST /api/logs/export - 导出日志为JSON文件
- POST /api/logs/import - 导入日志记录
"""