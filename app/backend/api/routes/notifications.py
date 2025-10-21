"""
通知系统API路由

功能：
1. 通知规则管理（CRUD）
2. 通知历史查询
3. 测试通知发送
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Any
from pydantic import BaseModel, Field

from database import get_db
from api.dependencies import get_current_user
from services.notification_service import NotificationService, NotificationType, NotificationChannel
from models import NotificationRule, NotificationLog
from log_manager import get_logger

logger = get_logger('notifications_api', 'enhanced_bot.log')

router = APIRouter(tags=["通知系统"])


# ==================== Pydantic 模型 ====================

class NotificationRuleCreate(BaseModel):
    """创建通知规则请求"""
    notification_type: str = Field(..., description="通知类型")
    notification_types: Optional[List[str]] = Field(None, description="通知类型列表（可多选，存在时优先生效）")
    is_active: bool = Field(..., description="是否启用规则")
    user_id: Optional[int] = Field(None, description="用户ID（NULL表示全局规则）")
    
    # 通知渠道配置
    telegram_chat_id: Optional[str] = Field(None, description="Telegram聊天ID")
    telegram_client_id: Optional[str] = Field(None, description="发送所用Telegram客户端ID")
    telegram_client_type: Optional[str] = Field(None, description="发送所用Telegram客户端类型（user/bot）")
    telegram_enabled: bool = Field(False, description="是否启用Telegram通知")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    webhook_enabled: bool = Field(False, description="是否启用Webhook")
    email_address: Optional[str] = Field(None, description="邮箱地址")
    email_enabled: bool = Field(False, description="是否启用邮件通知")
    
    # 通知频率控制
    min_interval: int = Field(0, description="最小间隔（秒），0表示不限制")
    max_per_hour: int = Field(0, description="每小时最大数量，0表示不限制")
    
    # 通知内容配置
    custom_template: Optional[str] = Field(None, description="自定义模板")
    include_details: bool = Field(True, description="是否包含详细信息")


class NotificationRuleUpdate(BaseModel):
    """更新通知规则请求"""
    is_active: Optional[bool] = None
    notification_types: Optional[List[str]] = None
    telegram_chat_id: Optional[str] = None
    telegram_client_id: Optional[str] = None
    telegram_client_type: Optional[str] = None
    telegram_enabled: Optional[bool] = None
    webhook_url: Optional[str] = None
    webhook_enabled: Optional[bool] = None
    email_address: Optional[str] = None
    email_enabled: Optional[bool] = None
    min_interval: Optional[int] = None
    max_per_hour: Optional[int] = None
    custom_template: Optional[str] = None
    include_details: Optional[bool] = None


class TestNotificationRequest(BaseModel):
    """测试通知请求"""
    notification_type: str = Field(..., description="通知类型")
    channels: List[str] = Field(default=["telegram"], description="通知渠道")
    test_data: dict = Field(default={}, description="测试数据")


# ==================== 通知规则管理 ====================

@router.post("/rules")
async def create_notification_rule(
    rule_data: NotificationRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """创建通知规则"""
    try:
        service = NotificationService(db)
        
        rule = await service.create_rule(
            notification_type=rule_data.notification_type,
            user_id=rule_data.user_id,
            is_active=rule_data.is_active,
            notification_types=rule_data.notification_types,
            telegram_chat_id=rule_data.telegram_chat_id,
            telegram_client_id=rule_data.telegram_client_id,
            telegram_client_type=rule_data.telegram_client_type,
            telegram_enabled=rule_data.telegram_enabled,
            webhook_url=rule_data.webhook_url,
            webhook_enabled=rule_data.webhook_enabled,
            email_address=rule_data.email_address,
            email_enabled=rule_data.email_enabled,
            min_interval=rule_data.min_interval,
            max_per_hour=rule_data.max_per_hour,
            custom_template=rule_data.custom_template,
            include_details=rule_data.include_details
        )
        
        return {
            "success": True,
            "message": "通知规则创建成功",
            "data": {
                "id": rule.id,
                "notification_type": rule.notification_type,
                "notification_types": getattr(rule, 'notification_types', None),
                "is_active": rule.is_active,
                "telegram_client_id": getattr(rule, 'telegram_client_id', None),
                "telegram_client_type": getattr(rule, 'telegram_client_type', None),
                "telegram_enabled": rule.telegram_enabled,
                "webhook_enabled": rule.webhook_enabled,
                "email_enabled": rule.email_enabled,
                "created_at": rule.created_at.isoformat() if rule.created_at else None
            }
        }
        
    except Exception as e:
        logger.error(f"创建通知规则失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules")
async def get_notification_rules(
    notification_type: Optional[str] = None,
    user_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """获取通知规则列表"""
    try:
        from sqlalchemy import select, and_
        
        query = select(NotificationRule)
        
        conditions = []
        if notification_type:
            conditions.append(NotificationRule.notification_type == notification_type)
        if user_id is not None:
            conditions.append(NotificationRule.user_id == user_id)
        if is_active is not None:
            conditions.append(NotificationRule.is_active == is_active)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await db.execute(query)
        rules = result.scalars().all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": rule.id,
                    "user_id": rule.user_id,
                    "notification_type": rule.notification_type,
                    "notification_types": getattr(rule, 'notification_types', None),
                    "is_active": rule.is_active,
                    "telegram_chat_id": rule.telegram_chat_id,
                    "telegram_client_id": getattr(rule, 'telegram_client_id', None),
                    "telegram_client_type": getattr(rule, 'telegram_client_type', None),
                    "telegram_enabled": rule.telegram_enabled,
                    "webhook_url": rule.webhook_url,
                    "webhook_enabled": rule.webhook_enabled,
                    "email_address": rule.email_address,
                    "email_enabled": rule.email_enabled,
                    "min_interval": rule.min_interval,
                    "max_per_hour": rule.max_per_hour,
                    "last_sent_at": rule.last_sent_at.isoformat() if rule.last_sent_at else None,
                    "sent_count_hour": rule.sent_count_hour,
                    "custom_template": rule.custom_template,
                    "include_details": rule.include_details,
                    "created_at": rule.created_at.isoformat() if rule.created_at else None,
                    "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
                }
                for rule in rules
            ]
        }
        
    except Exception as e:
        logger.error(f"获取通知规则列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}")
async def get_notification_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """获取指定通知规则"""
    try:
        service = NotificationService(db)
        rule = await service.get_rule(rule_id)
        
        if not rule:
            raise HTTPException(status_code=404, detail="通知规则不存在")
        
        return {
            "success": True,
            "data": {
                "id": rule.id,
                "user_id": rule.user_id,
                "notification_type": rule.notification_type,
                "notification_types": getattr(rule, 'notification_types', None),
                "is_active": rule.is_active,
                "telegram_client_id": getattr(rule, 'telegram_client_id', None),
                "telegram_client_type": getattr(rule, 'telegram_client_type', None),
                "telegram_chat_id": rule.telegram_chat_id,
                "telegram_enabled": rule.telegram_enabled,
                "webhook_url": rule.webhook_url,
                "webhook_enabled": rule.webhook_enabled,
                "email_address": rule.email_address,
                "email_enabled": rule.email_enabled,
                "min_interval": rule.min_interval,
                "max_per_hour": rule.max_per_hour,
                "last_sent_at": rule.last_sent_at.isoformat() if rule.last_sent_at else None,
                "sent_count_hour": rule.sent_count_hour,
                "custom_template": rule.custom_template,
                "include_details": rule.include_details,
                "created_at": rule.created_at.isoformat() if rule.created_at else None,
                "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取通知规则失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}")
async def update_notification_rule(
    rule_id: int,
    rule_data: NotificationRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """更新通知规则"""
    try:
        service = NotificationService(db)
        
        # 只更新非None的字段
        update_data = {k: v for k, v in rule_data.dict().items() if v is not None}
        
        rule = await service.update_rule(rule_id, **update_data)
        
        if not rule:
            raise HTTPException(status_code=404, detail="通知规则不存在")
        
        return {
            "success": True,
            "message": "通知规则更新成功",
            "data": {
                "id": rule.id,
                "notification_type": rule.notification_type,
                "is_active": rule.is_active,
                "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新通知规则失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_notification_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """删除通知规则"""
    try:
        service = NotificationService(db)
        success = await service.delete_rule(rule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="通知规则不存在")
        
        return {
            "success": True,
            "message": "通知规则删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除通知规则失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/{rule_id}/toggle")
async def toggle_notification_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """切换通知规则启用状态"""
    try:
        service = NotificationService(db)
        rule = await service.get_rule(rule_id)
        
        if not rule:
            raise HTTPException(status_code=404, detail="通知规则不存在")
        
        # 切换状态
        rule = await service.update_rule(rule_id, is_active=not rule.is_active)
        
        return {
            "success": True,
            "message": f"通知规则已{'启用' if rule.is_active else '禁用'}",
            "data": {
                "id": rule.id,
                "is_active": rule.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换通知规则状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 通知历史查询 ====================

@router.get("/logs")
async def get_notification_logs(
    notification_type: Optional[str] = None,
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """获取通知历史"""
    try:
        from sqlalchemy import select, and_
        
        query = select(NotificationLog).order_by(NotificationLog.sent_at.desc())
        
        conditions = []
        if notification_type:
            conditions.append(NotificationLog.notification_type == notification_type)
        if user_id is not None:
            conditions.append(NotificationLog.user_id == user_id)
        if status:
            conditions.append(NotificationLog.status == status)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": log.id,
                    "notification_type": log.notification_type,
                    "message": log.message,
                    "channels": log.channels,
                    "user_id": log.user_id,
                    "status": log.status,
                    "error_message": log.error_message,
                    "related_type": log.related_type,
                    "related_id": log.related_id,
                    "sent_at": log.sent_at.isoformat() if log.sent_at else None
                }
                for log in logs
            ]
        }
        
    except Exception as e:
        logger.error(f"获取通知历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{log_id}")
async def get_notification_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """获取指定通知历史"""
    try:
        from sqlalchemy import select
        
        result = await db.execute(
            select(NotificationLog).where(NotificationLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        
        if not log:
            raise HTTPException(status_code=404, detail="通知历史不存在")
        
        return {
            "success": True,
            "data": {
                "id": log.id,
                "notification_type": log.notification_type,
                "message": log.message,
                "channels": log.channels,
                "user_id": log.user_id,
                "status": log.status,
                "error_message": log.error_message,
                "related_type": log.related_type,
                "related_id": log.related_id,
                "sent_at": log.sent_at.isoformat() if log.sent_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取通知历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 测试和统计 ====================

@router.post("/test")
async def test_notification(
    test_data: TestNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """测试通知发送"""
    try:
        service = NotificationService(db)
        
        # 验证通知类型
        try:
            notification_type = NotificationType(test_data.notification_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的通知类型")
        
        # 验证通知渠道
        channels = []
        for channel_str in test_data.channels:
            try:
                channels.append(NotificationChannel(channel_str))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的通知渠道: {channel_str}")
        
        # 准备测试数据
        data = test_data.test_data or {
            "rule_name": "测试规则",
            "test_message": "这是一条测试通知",
            "test_time": "2025-01-14 16:00:00"
        }
        
        # 发送测试通知
        success = await service.send_notification(
            notification_type=notification_type,
            data=data,
            channels=channels,
            user_id=current_user.id if hasattr(current_user, 'id') else None
        )
        
        return {
            "success": success,
            "message": "测试通知发送成功" if success else "测试通知发送失败"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试通知发送失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_notification_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """获取通知统计"""
    try:
        from sqlalchemy import select, func
        
        # 总规则数
        total_rules = await db.scalar(select(func.count(NotificationRule.id)))
        
        # 活跃规则数
        active_rules = await db.scalar(
            select(func.count(NotificationRule.id)).where(NotificationRule.is_active == True)
        )
        
        # 总通知数
        total_notifications = await db.scalar(select(func.count(NotificationLog.id)))
        
        # 成功通知数
        successful_notifications = await db.scalar(
            select(func.count(NotificationLog.id)).where(NotificationLog.status == 'sent')
        )
        
        # 失败通知数
        failed_notifications = await db.scalar(
            select(func.count(NotificationLog.id)).where(NotificationLog.status == 'failed')
        )
        
        # 按类型统计
        type_stats_result = await db.execute(
            select(
                NotificationLog.notification_type,
                func.count(NotificationLog.id).label('count')
            ).group_by(NotificationLog.notification_type)
        )
        type_stats = {row[0]: row[1] for row in type_stats_result.fetchall()}
        
        return {
            "success": True,
            "data": {
                "total_rules": total_rules or 0,
                "active_rules": active_rules or 0,
                "inactive_rules": (total_rules or 0) - (active_rules or 0),
                "total_notifications": total_notifications or 0,
                "successful_notifications": successful_notifications or 0,
                "failed_notifications": failed_notifications or 0,
                "success_rate": round((successful_notifications / total_notifications * 100), 2) if total_notifications else 0,
                "type_stats": type_stats
            }
        }
        
    except Exception as e:
        logger.error(f"获取通知统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_notification_types(
    current_user: Any = Depends(get_current_user)
):
    """获取所有可用的通知类型"""
    return {
        "success": True,
        "data": [
            {
                "value": nt.value,
                "label": nt.value.replace('_', ' ').title(),
                "description": _get_type_description(nt)
            }
            for nt in NotificationType
        ]
    }


def _get_type_description(notification_type: NotificationType) -> str:
    """获取通知类型描述"""
    descriptions = {
        NotificationType.RESOURCE_CAPTURED: "资源链接捕获时通知",
        NotificationType.SAVE_115_SUCCESS: "115转存成功时通知",
        NotificationType.SAVE_115_FAILED: "115转存失败时通知",
        NotificationType.DOWNLOAD_COMPLETE: "媒体下载完成时通知",
        NotificationType.DOWNLOAD_FAILED: "媒体下载失败时通知",
        NotificationType.DOWNLOAD_PROGRESS: "媒体下载进度更新时通知",
        NotificationType.FORWARD_SUCCESS: "消息转发成功时通知",
        NotificationType.FORWARD_FAILED: "消息转发失败时通知",
        NotificationType.TASK_STALE: "任务卡住时通知",
        NotificationType.STORAGE_WARNING: "存储空间不足时通知",
        NotificationType.DAILY_REPORT: "每日统计报告",
        NotificationType.SYSTEM_ERROR: "系统错误时通知"
    }
    return descriptions.get(notification_type, "")

