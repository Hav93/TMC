"""
资源监控 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import List, Optional
from datetime import datetime, timedelta
import json

from database import get_db
from models import ResourceMonitorRule, ResourceRecord
from log_manager import get_logger
from timezone_utils import get_user_now

logger = get_logger("resource_monitor_api", "web_api.log")

router = APIRouter()


# ==================== 规则管理 ====================

@router.get("/rules")
async def get_rules(
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取资源监控规则列表"""
    try:
        query = select(ResourceMonitorRule)
        if is_active is not None:
            query = query.where(ResourceMonitorRule.is_active == is_active)
        
        query = query.order_by(desc(ResourceMonitorRule.created_at))
        result = await db.execute(query)
        rules = result.scalars().all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": rule.id,
                    "name": rule.name,
                    "source_chats": json.loads(rule.source_chats) if rule.source_chats else [],
                    "is_active": rule.is_active,
                    "link_types": json.loads(rule.link_types) if rule.link_types else [],
                    "keywords": json.loads(rule.keywords) if rule.keywords else [],
                    "auto_save_to_115": rule.auto_save_to_115,
                    "target_path": rule.target_path,
                    "target_path_pan115": getattr(rule, 'target_path_pan115', None),
                    "target_path_magnet": getattr(rule, 'target_path_magnet', None),
                    "target_path_ed2k": getattr(rule, 'target_path_ed2k', None),
                    "default_tags": json.loads(rule.default_tags) if rule.default_tags else [],
                    "enable_deduplication": rule.enable_deduplication,
                    "dedup_time_window": rule.dedup_time_window,
                    "created_at": rule.created_at.isoformat() if rule.created_at else None,
                    "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
                }
                for rule in rules
            ]
        }
    except Exception as e:
        logger.error(f"获取规则列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules")
async def create_rule(
    rule_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """创建资源监控规则"""
    try:
        rule = ResourceMonitorRule(
            name=rule_data.get("name"),
            source_chats=json.dumps(rule_data.get("source_chats", []), ensure_ascii=False),
            is_active=rule_data.get("is_active", True),
            link_types=json.dumps(rule_data.get("link_types", []), ensure_ascii=False),
            keywords=json.dumps(rule_data.get("keywords", []), ensure_ascii=False),
            auto_save_to_115=rule_data.get("auto_save_to_115", False),
            target_path=rule_data.get("target_path"),
            target_path_pan115=rule_data.get("target_path_pan115"),
            target_path_magnet=rule_data.get("target_path_magnet"),
            target_path_ed2k=rule_data.get("target_path_ed2k"),
            pan115_user_key=None,  # 不再保存user_key，使用系统设置中的115账号
            default_tags=json.dumps(rule_data.get("default_tags", []), ensure_ascii=False),
            enable_deduplication=rule_data.get("enable_deduplication", True),
            dedup_time_window=rule_data.get("dedup_time_window", 3600)
        )
        
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        
        logger.info(f"✅ 创建资源监控规则: {rule.name} (使用系统115账号)")
        
        return {
            "success": True,
            "message": "规则创建成功",
            "data": {"id": rule.id}
        }
    except Exception as e:
        logger.error(f"创建规则失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    rule_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """更新资源监控规则"""
    try:
        result = await db.execute(
            select(ResourceMonitorRule).where(ResourceMonitorRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
        
        # 更新字段
        if "name" in rule_data:
            rule.name = rule_data["name"]
        if "source_chats" in rule_data:
            rule.source_chats = json.dumps(rule_data["source_chats"], ensure_ascii=False)
        if "is_active" in rule_data:
            rule.is_active = rule_data["is_active"]
        if "link_types" in rule_data:
            rule.link_types = json.dumps(rule_data["link_types"], ensure_ascii=False)
        if "keywords" in rule_data:
            rule.keywords = json.dumps(rule_data["keywords"], ensure_ascii=False)
        if "auto_save_to_115" in rule_data:
            rule.auto_save_to_115 = rule_data["auto_save_to_115"]
        if "target_path" in rule_data:
            rule.target_path = rule_data["target_path"]
        if "target_path_pan115" in rule_data:
            rule.target_path_pan115 = rule_data["target_path_pan115"]
        if "target_path_magnet" in rule_data:
            rule.target_path_magnet = rule_data["target_path_magnet"]
        if "target_path_ed2k" in rule_data:
            rule.target_path_ed2k = rule_data["target_path_ed2k"]
        if "default_tags" in rule_data:
            rule.default_tags = json.dumps(rule_data["default_tags"], ensure_ascii=False)
        if "enable_deduplication" in rule_data:
            rule.enable_deduplication = rule_data["enable_deduplication"]
        if "dedup_time_window" in rule_data:
            rule.dedup_time_window = rule_data["dedup_time_window"]
        
        rule.updated_at = get_user_now()
        await db.commit()
        
        logger.info(f"✅ 更新资源监控规则: {rule.name}")
        
        return {"success": True, "message": "规则更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新规则失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除资源监控规则"""
    try:
        result = await db.execute(
            select(ResourceMonitorRule).where(ResourceMonitorRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
        
        await db.delete(rule)
        await db.commit()
        
        logger.info(f"✅ 删除资源监控规则: {rule.name}")
        
        return {"success": True, "message": "规则删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除规则失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 资源记录管理 ====================

@router.get("/records")
async def get_records(
    rule_id: Optional[int] = None,
    save_status: Optional[str] = None,
    link_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取资源记录列表"""
    try:
        # 构建查询
        query = select(ResourceRecord)
        
        if rule_id is not None:
            query = query.where(ResourceRecord.rule_id == rule_id)
        if save_status:
            query = query.where(ResourceRecord.save_status == save_status)
        if link_type:
            query = query.where(ResourceRecord.link_type == link_type)
        if search:
            query = query.where(ResourceRecord.message_text.like(f"%{search}%"))
        
        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        query = query.order_by(desc(ResourceRecord.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        records = result.scalars().all()
        
        return {
            "success": True,
            "data": {
                "records": [
                    {
                        "id": record.id,
                        "rule_id": record.rule_id,
                        "rule_name": record.rule_name,
                        "source_chat_id": record.source_chat_id,
                        "source_chat_name": getattr(record, 'source_chat_name', None),
                        "message_id": record.message_id,
                        "message_text": record.message_text,
                        "message_date": record.message_date.isoformat() if record.message_date else None,
                        "link_type": record.link_type,
                        "link_url": record.link_url,
                        "link_hash": getattr(record, 'link_hash', None),
                        "save_status": record.save_status,
                        "save_path": record.save_path,
                        "save_error": record.save_error,
                        "save_time": record.save_time.isoformat() if record.save_time else None,
                        "retry_count": record.retry_count or 0,
                        "tags": json.loads(record.tags) if record.tags else [],
                        "created_at": record.created_at.isoformat() if record.created_at else None,
                        "updated_at": record.updated_at.isoformat() if getattr(record, 'updated_at', None) else None
                    }
                    for record in records
                ],
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        }
    except Exception as e:
        logger.error(f"获取记录列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records/{record_id}")
async def get_record(
    record_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取资源记录详情"""
    try:
        result = await db.execute(
            select(ResourceRecord).where(ResourceRecord.id == record_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")
        
        return {
            "success": True,
            "data": {
                "id": record.id,
                "rule_id": record.rule_id,
                "rule_name": record.rule_name,
                "source_chat_id": record.source_chat_id,
                "message_id": record.message_id,
                "message_text": record.message_text,
                "message_date": record.message_date.isoformat() if record.message_date else None,
                "link_type": record.link_type,
                "link_url": record.link_url,
                "save_status": record.save_status,
                "save_path": record.save_path,
                "save_error": record.save_error,
                "save_time": record.save_time.isoformat() if record.save_time else None,
                "retry_count": record.retry_count,
                "tags": json.loads(record.tags) if record.tags else [],
                "message_snapshot": json.loads(record.message_snapshot) if record.message_snapshot else {},
                "created_at": record.created_at.isoformat() if record.created_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取记录详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/records/clear")
async def clear_records(
    rule_id: Optional[int] = Query(None, description="规则ID，如果指定则只清空该规则的记录"),
    save_status: Optional[str] = Query(None, description="转存状态过滤(pending/success/failed)"),
    db: AsyncSession = Depends(get_db)
):
    """清空资源记录（支持按规则或状态过滤）"""
    try:
        # 构建删除查询
        query = select(ResourceRecord)
        
        if rule_id is not None:
            query = query.where(ResourceRecord.rule_id == rule_id)
        
        if save_status:
            query = query.where(ResourceRecord.save_status == save_status)
        
        # 获取要删除的记录
        result = await db.execute(query)
        records = result.scalars().all()
        
        deleted_count = len(records)
        
        # 删除记录
        for record in records:
            await db.delete(record)
        
        await db.commit()
        
        filter_info = []
        if rule_id:
            filter_info.append(f"规则ID={rule_id}")
        if save_status:
            filter_info.append(f"状态={save_status}")
        
        filter_str = f" ({', '.join(filter_info)})" if filter_info else ""
        
        logger.info(f"✅ 清空资源记录成功{filter_str}: 删除了 {deleted_count} 条记录")
        
        return {
            "success": True,
            "message": f"成功清空 {deleted_count} 条记录{filter_str}",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"清空记录失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/records/{record_id}")
async def delete_record(
    record_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除单个资源记录"""
    try:
        # 查找记录
        result = await db.execute(
            select(ResourceRecord).where(ResourceRecord.id == record_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")
        
        # 删除记录
        await db.delete(record)
        await db.commit()
        
        logger.info(f"✅ 删除资源记录成功: record_id={record_id}")
        
        return {
            "success": True,
            "message": "记录删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除记录失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/records/{record_id}/retry")
async def retry_resource_record(
    record_id: int,
    db: AsyncSession = Depends(get_db)
):
    """重试失败的资源记录（推送到115）"""
    try:
        # 查找记录
        result = await db.execute(
            select(ResourceRecord).where(ResourceRecord.id == record_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")
        
        # 检查记录状态
        if record.save_status == 'success':
            return {
                "success": False,
                "message": "该记录已经成功，无需重试"
            }
        
        # 重置状态为待处理
        record.save_status = 'pending'
        record.save_error = None
        record.updated_at = get_user_now()
        
        await db.commit()
        await db.refresh(record)
        
        logger.info(f"✅ 资源记录已重置为待处理状态: record_id={record_id}")
        
        # TODO: 这里可以触发后台任务重新处理
        # 或者返回信息让前端知道需要等待后台任务处理
        
        return {
            "success": True,
            "message": "记录已重置，等待后台处理",
            "data": {
                "id": record.id,
                "save_status": record.save_status
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重试记录失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/records/batch-delete")
async def batch_delete_records(
    data: dict,
    db: AsyncSession = Depends(get_db)
):
    """批量删除资源记录"""
    try:
        record_ids = data.get("record_ids", [])
        
        if not record_ids:
            raise HTTPException(status_code=400, detail="请提供要删除的记录ID列表")
        
        # 查找并删除记录
        result = await db.execute(
            select(ResourceRecord).where(ResourceRecord.id.in_(record_ids))
        )
        records = result.scalars().all()
        
        deleted_count = len(records)
        
        for record in records:
            await db.delete(record)
        
        await db.commit()
        
        logger.info(f"✅ 批量删除资源记录成功: 删除了 {deleted_count} 条记录")
        
        return {
            "success": True,
            "message": f"成功删除 {deleted_count} 条记录",
            "deleted_count": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除记录失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计信息 ====================

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取资源监控统计"""
    try:
        # 规则统计
        rules_total = await db.execute(select(func.count()).select_from(ResourceMonitorRule))
        rules_active = await db.execute(
            select(func.count()).select_from(ResourceMonitorRule).where(ResourceMonitorRule.is_active == True)
        )
        
        # 记录统计
        records_total = await db.execute(select(func.count()).select_from(ResourceRecord))
        records_pending = await db.execute(
            select(func.count()).select_from(ResourceRecord).where(ResourceRecord.save_status == 'pending')
        )
        records_success = await db.execute(
            select(func.count()).select_from(ResourceRecord).where(ResourceRecord.save_status == 'success')
        )
        records_failed = await db.execute(
            select(func.count()).select_from(ResourceRecord).where(ResourceRecord.save_status == 'failed')
        )
        
        return {
            "success": True,
            "data": {
                "total_rules": rules_total.scalar(),
                "active_rules": rules_active.scalar(),
                "total_records": records_total.scalar(),
                "saved_records": records_success.scalar(),
                "failed_records": records_failed.scalar()
            }
        }
    except Exception as e:
        logger.error(f"获取统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

