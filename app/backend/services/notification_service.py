"""
推送通知服务

功能：
1. 多渠道推送（Telegram/Webhook/Email）
2. 模板化消息
3. 通知规则管理
4. 通知历史记录
5. 频率控制
"""
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import timedelta
import asyncio
import json
from timezone_utils import get_user_now
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from log_manager import get_logger
from database import get_db
from models import NotificationRule, NotificationLog, get_local_now
from telegram_client_manager import multi_client_manager

logger = get_logger("notification", "enhanced_bot.log")


class NotificationType(Enum):
    """通知类型"""
    # 资源监控相关
    RESOURCE_CAPTURED = "resource_captured"          # 资源捕获
    SAVE_115_SUCCESS = "save_115_success"            # 115转存成功
    SAVE_115_FAILED = "save_115_failed"              # 115转存失败
    
    # 媒体监控相关
    DOWNLOAD_COMPLETE = "download_complete"          # 下载完成
    DOWNLOAD_FAILED = "download_failed"              # 下载失败
    DOWNLOAD_PROGRESS = "download_progress"          # 下载进度（可选）
    
    # 消息转发相关
    FORWARD_SUCCESS = "forward_success"              # 转发成功
    FORWARD_FAILED = "forward_failed"                # 转发失败
    
    # 系统相关
    TASK_STALE = "task_stale"                        # 任务卡住
    STORAGE_WARNING = "storage_warning"              # 存储空间警告
    DAILY_REPORT = "daily_report"                    # 每日报告
    SYSTEM_ERROR = "system_error"                    # 系统错误


class NotificationChannel(Enum):
    """通知渠道"""
    TELEGRAM = "telegram"        # Telegram消息
    WEBHOOK = "webhook"          # Webhook
    EMAIL = "email"              # 邮件


class NotificationService:
    """
    推送通知服务
    
    功能：
    1. 多渠道推送（Telegram/Webhook/Email）
    2. 模板化消息
    3. 通知规则管理
    4. 通知历史记录
    5. 频率控制
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._telegram_client = None  # 延迟初始化
    
    def set_telegram_client(self, client_manager):
        """设置Telegram客户端管理器"""
        self._telegram_client = client_manager
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        data: Dict[str, Any],
        channels: Optional[List[NotificationChannel]] = None,
        user_id: Optional[int] = None,
        related_type: Optional[str] = None,
        related_id: Optional[int] = None
    ) -> bool:
        """
        发送通知
        
        Args:
            notification_type: 通知类型
            data: 通知数据
            channels: 通知渠道（None表示使用规则配置的渠道）
            user_id: 用户ID（None表示发送给所有用户）
            related_type: 关联类型（resource/media/forward）
            related_id: 关联ID
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 1. 获取适用的通知规则
            rules = await self._get_applicable_rules(notification_type, user_id)
            if not rules:
                logger.debug(f"没有适用的通知规则: {notification_type.value}")
                return False
            
            # 2. 检查频率限制
            valid_rules = []
            for rule in rules:
                if await self._check_rate_limit(rule):
                    valid_rules.append(rule)
                else:
                    logger.debug(f"规则 {rule.id} 触发频率限制")
            
            if not valid_rules:
                logger.debug(f"所有规则都触发频率限制: {notification_type.value}")
                return False
            
            # 3. 生成通知内容
            from services.notification_templates import NotificationTemplateEngine
            template_engine = NotificationTemplateEngine()
            message = template_engine.render(notification_type, data)
            
            # 4. 确定通知渠道
            if channels is None:
                channels = self._get_enabled_channels(valid_rules[0])
            
            if not channels:
                logger.debug(f"没有启用的通知渠道")
                return False
            
            # 5. 发送到各个渠道
            success = False
            sent_channels = []
            for channel in channels:
                try:
                    if await self._send_to_channel(channel, message, data, valid_rules[0]):
                        sent_channels.append(channel.value)
                        success = True
                except Exception as e:
                    logger.error(f"发送到渠道 {channel.value} 失败: {e}")
            
            # 6. 更新规则的发送统计
            for rule in valid_rules:
                await self._update_rule_stats(rule)
            
            # 7. 记录通知历史
            await self._log_notification(
                notification_type=notification_type,
                message=message,
                channels=sent_channels,
                user_id=user_id,
                status='sent' if success else 'failed',
                related_type=related_type,
                related_id=related_id
            )
            
            if success:
                logger.info(f"✅ 通知发送成功: {notification_type.value} -> {', '.join(sent_channels)}")
            else:
                logger.warning(f"⚠️ 通知发送失败: {notification_type.value}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 通知发送异常: {e}", exc_info=True)
            return False
    
    async def _get_applicable_rules(
        self, 
        notification_type: NotificationType,
        user_id: Optional[int] = None
    ) -> List[NotificationRule]:
        """获取适用的通知规则（支持单类型与多类型规则）"""
        try:
            # 先取所有激活规则，后在内存中过滤（规则量通常很小）
            query = select(NotificationRule).where(NotificationRule.is_active == True)
            if user_id is not None:
                query = query.where((NotificationRule.user_id == user_id) | (NotificationRule.user_id == None))
            else:
                query = query.where(NotificationRule.user_id == None)
            result = await self.db.execute(query)
            all_rules = list(result.scalars().all())

            wanted = notification_type.value
            applicable: List[NotificationRule] = []
            for rule in all_rules:
                try:
                    if rule.notification_type == wanted:
                        applicable.append(rule)
                        continue
                    if getattr(rule, 'notification_types', None):
                        types = json.loads(rule.notification_types) if isinstance(rule.notification_types, str) else (rule.notification_types or [])
                        if wanted in types:
                            applicable.append(rule)
                except Exception:
                    # 解析失败时忽略该规则的多类型字段
                    pass
            return applicable
        except Exception as e:
            logger.error(f"获取通知规则失败: {e}", exc_info=True)
            return []
    
    async def _check_rate_limit(self, rule: NotificationRule) -> bool:
        """检查频率限制"""
        try:
            now = get_local_now()
            
            # 检查最小间隔
            if rule.min_interval > 0 and rule.last_sent_at:
                time_since_last = (now - rule.last_sent_at).total_seconds()
                if time_since_last < rule.min_interval:
                    return False
            
            # 检查每小时最大数量
            if rule.max_per_hour > 0:
                # 检查是否需要重置小时计数器
                if rule.hour_reset_at is None or now >= rule.hour_reset_at:
                    rule.sent_count_hour = 0
                    rule.hour_reset_at = now + timedelta(hours=1)
                    await self.db.commit()
                
                # 检查是否超过限制
                if rule.sent_count_hour >= rule.max_per_hour:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查频率限制失败: {e}", exc_info=True)
            return True  # 出错时允许发送
    
    def _get_enabled_channels(self, rule: NotificationRule) -> List[NotificationChannel]:
        """获取启用的通知渠道"""
        channels = []
        
        if rule.telegram_enabled and rule.telegram_chat_id:
            channels.append(NotificationChannel.TELEGRAM)
        
        if rule.webhook_enabled and rule.webhook_url:
            channels.append(NotificationChannel.WEBHOOK)
        
        if rule.email_enabled and rule.email_address:
            channels.append(NotificationChannel.EMAIL)
        
        return channels
    
    async def _send_to_channel(
        self,
        channel: NotificationChannel,
        message: str,
        data: Dict[str, Any],
        rule: NotificationRule
    ) -> bool:
        """发送到指定渠道"""
        try:
            if channel == NotificationChannel.TELEGRAM:
                return await self._send_telegram(message, rule.telegram_chat_id)
            
            elif channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook(message, data, rule.webhook_url)
            
            elif channel == NotificationChannel.EMAIL:
                return await self._send_email(message, rule.email_address)
            
            else:
                logger.warning(f"不支持的通知渠道: {channel}")
                return False
                
        except Exception as e:
            logger.error(f"发送到渠道 {channel.value} 失败: {e}", exc_info=True)
            return False
    
    async def _send_telegram(self, message: str, chat_id: str) -> bool:
        """发送Telegram消息"""
        try:
            # 优先使用显式设置的客户端
            if self._telegram_client:
                await self._telegram_client.send_message(
                    chat_id=int(chat_id),
                    message=message
                )
                return True
            
            # 回退：使用全局多客户端管理器中第一个已连接的客户端
            for _, client in multi_client_manager.clients.items():
                if client and client.connected:
                    await client._safe_send_message(int(chat_id), message)
                    return True
            
            logger.warning("Telegram无可用客户端：未初始化或未连接")
            
        except Exception as e:
            logger.error(f"发送Telegram消息失败: {e}", exc_info=True)
            return False
    
    async def _send_webhook(self, message: str, data: Dict[str, Any], webhook_url: str) -> bool:
        """发送Webhook"""
        try:
            import aiohttp
            
            payload = {
                "message": message,
                "data": data,
                "timestamp": get_user_now().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        logger.warning(f"Webhook返回非200状态: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"发送Webhook失败: {e}", exc_info=True)
            return False
    
    async def _send_email(self, message: str, email_address: str) -> bool:
        """发送邮件"""
        try:
            # TODO: 实现邮件发送功能
            # 这里需要配置SMTP服务器
            logger.info(f"邮件发送功能待实现: {email_address}")
            return False
            
        except Exception as e:
            logger.error(f"发送邮件失败: {e}", exc_info=True)
            return False
    
    async def _update_rule_stats(self, rule: NotificationRule):
        """更新规则的发送统计"""
        try:
            rule.last_sent_at = get_local_now()
            rule.sent_count_hour += 1
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"更新规则统计失败: {e}", exc_info=True)
            await self.db.rollback()
    
    async def _log_notification(
        self,
        notification_type: NotificationType,
        message: str,
        channels: List[str],
        user_id: Optional[int],
        status: str,
        related_type: Optional[str] = None,
        related_id: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """记录通知历史"""
        try:
            log = NotificationLog(
                notification_type=notification_type.value,
                message=message,
                channels=','.join(channels) if channels else None,
                user_id=user_id,
                status=status,
                error_message=error_message,
                related_type=related_type,
                related_id=related_id,
                sent_at=get_local_now()
            )
            
            self.db.add(log)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"记录通知历史失败: {e}", exc_info=True)
            await self.db.rollback()
    
    # ==================== 规则管理方法 ====================
    
    async def create_rule(
        self,
        notification_type: str,
        is_active: bool,
        user_id: Optional[int] = None,
        telegram_chat_id: Optional[str] = None,
        telegram_enabled: bool = False,
        webhook_url: Optional[str] = None,
        webhook_enabled: bool = False,
        email_address: Optional[str] = None,
        email_enabled: bool = False,
        min_interval: int = 0,
        max_per_hour: int = 0,
        custom_template: Optional[str] = None,
        include_details: bool = True,
        notification_types: Optional[List[str]] = None
    ) -> NotificationRule:
        """创建通知规则"""
        try:
            rule = NotificationRule(
                user_id=user_id,
                notification_type=notification_type,
                notification_types=json.dumps(notification_types, ensure_ascii=False) if notification_types else None,
                is_active=is_active,
                telegram_chat_id=telegram_chat_id,
                telegram_enabled=telegram_enabled,
                webhook_url=webhook_url,
                webhook_enabled=webhook_enabled,
                email_address=email_address,
                email_enabled=email_enabled,
                min_interval=min_interval,
                max_per_hour=max_per_hour,
                custom_template=custom_template,
                include_details=include_details,
                sent_count_hour=0
            )
            
            self.db.add(rule)
            await self.db.commit()
            await self.db.refresh(rule)
            
            logger.info(f"✅ 创建通知规则成功: {rule.id}")
            return rule
            
        except Exception as e:
            logger.error(f"❌ 创建通知规则失败: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def get_rule(self, rule_id: int) -> Optional[NotificationRule]:
        """获取通知规则"""
        try:
            result = await self.db.execute(
                select(NotificationRule).where(NotificationRule.id == rule_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"获取通知规则失败: {e}", exc_info=True)
            return None
    
    async def update_rule(self, rule_id: int, **kwargs) -> Optional[NotificationRule]:
        """更新通知规则"""
        try:
            rule = await self.get_rule(rule_id)
            if not rule:
                return None
            
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    if key == 'notification_types' and isinstance(value, list):
                        setattr(rule, key, json.dumps(value, ensure_ascii=False))
                    else:
                        setattr(rule, key, value)
            
            await self.db.commit()
            await self.db.refresh(rule)
            
            logger.info(f"✅ 更新通知规则成功: {rule_id}")
            return rule
            
        except Exception as e:
            logger.error(f"❌ 更新通知规则失败: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def delete_rule(self, rule_id: int) -> bool:
        """删除通知规则"""
        try:
            rule = await self.get_rule(rule_id)
            if not rule:
                return False
            
            await self.db.delete(rule)
            await self.db.commit()
            
            logger.info(f"✅ 删除通知规则成功: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 删除通知规则失败: {e}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def get_logs(
        self,
        notification_type: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[NotificationLog]:
        """获取通知历史"""
        try:
            query = select(NotificationLog).order_by(NotificationLog.sent_at.desc())
            
            if notification_type:
                query = query.where(NotificationLog.notification_type == notification_type)
            
            if user_id is not None:
                query = query.where(NotificationLog.user_id == user_id)
            
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"获取通知历史失败: {e}", exc_info=True)
            return []


# 全局单例（可选）
_notification_service_instance = None


def get_notification_service() -> Optional[NotificationService]:
    """获取通知服务单例"""
    return _notification_service_instance


def set_notification_service(service: NotificationService):
    """设置通知服务单例"""
    global _notification_service_instance
    _notification_service_instance = service


# 便捷函数：在非请求上下文中发送通知（自动管理数据库会话）
async def notify(
    notification_type: NotificationType,
    data: Dict[str, Any],
    channels: Optional[List[NotificationChannel]] = None,
    user_id: Optional[int] = None,
    related_type: Optional[str] = None,
    related_id: Optional[int] = None
) -> bool:
    async for db in get_db():
        service = NotificationService(db)
        # 尝试注入全局客户端（如果有）
        try:
            service.set_telegram_client(multi_client_manager)
        except Exception:
            pass
        return await service.send_notification(
            notification_type=notification_type,
            data=data,
            channels=channels,
            user_id=user_id,
            related_type=related_type,
            related_id=related_id
        )
    return False

