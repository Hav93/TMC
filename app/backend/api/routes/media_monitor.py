"""
媒体监控规则 API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List
from datetime import datetime
import json
import asyncio

from database import get_db
from models import MediaMonitorRule, User
from auth import get_current_user
from log_manager import get_logger
from telegram_client_manager import multi_client_manager

logger = get_logger('api.media_monitor')

router = APIRouter(tags=["media_monitor"])


async def notify_client_reload_chats(client_id: str):
    """通知客户端重新加载监听的聊天列表"""
    try:
        client_wrapper = multi_client_manager.get_client(client_id)
        if client_wrapper and client_wrapper.loop:
            # 在客户端的事件循环中执行更新
            asyncio.run_coroutine_threadsafe(
                client_wrapper._update_monitored_chats(),
                client_wrapper.loop
            )
            logger.info(f"✅ 已通知客户端 {client_id} 重新加载监听列表")
        else:
            logger.warning(f"⚠️ 客户端 {client_id} 未运行或事件循环不可用")
    except Exception as e:
        logger.error(f"❌ 通知客户端重新加载失败: {e}")


# ==================== 监控规则 API ====================

@router.get("/rules")
async def get_monitor_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    is_active: Optional[bool] = None,
    client_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取监控规则列表"""
    try:
        query = select(MediaMonitorRule)
        
        # 关键词搜索
        if keyword:
            query = query.where(
                or_(
                    MediaMonitorRule.name.contains(keyword),
                    MediaMonitorRule.description.contains(keyword)
                )
            )
        
        # 状态过滤
        if is_active is not None:
            query = query.where(MediaMonitorRule.is_active == is_active)
        
        # 客户端过滤
        if client_id:
            query = query.where(MediaMonitorRule.client_id == client_id)
        
        # 总数
        total_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(total_query)
        
        # 分页查询
        query = query.order_by(MediaMonitorRule.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        rules = result.scalars().all()
        
        return {
            "success": True,
            "rules": [rule_to_dict(rule) for rule in rules],
            "total": total or 0,
            "page": page,
            "page_size": page_size
        }
        
    except Exception as e:
        logger.error(f"获取监控规则列表失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"获取列表失败: {str(e)}"}
        )


@router.get("/rules/{rule_id}")
async def get_monitor_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取监控规则详情"""
    try:
        result = await db.execute(
            select(MediaMonitorRule).where(MediaMonitorRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "规则不存在"}
            )
        
        rule_dict = rule_to_dict(rule)
        logger.info(f"📤 返回规则详情: {rule_dict}")
        
        return {
            "success": True,
            "rule": rule_dict
        }
        
    except Exception as e:
        logger.error(f"获取监控规则详情失败: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"获取详情失败: {str(e)}"}
        )


@router.post("/rules")
async def create_monitor_rule(
    rule_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建监控规则"""
    try:
        # 验证必填字段
        if not rule_data.get('name'):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "规则名称不能为空"}
            )
        
        if not rule_data.get('client_id'):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "请选择客户端"}
            )
        
        # 创建规则对象
        rule = MediaMonitorRule(
            name=rule_data.get('name'),
            description=rule_data.get('description'),
            is_active=rule_data.get('is_active', True),
            client_id=rule_data.get('client_id'),
            
            # 监听源（前端已JSON化，直接保存）
            source_chats=rule_data.get('source_chats'),
            
            # 媒体过滤（前端已JSON化，直接保存）
            media_types=rule_data.get('media_types'),
            min_size_mb=rule_data.get('min_size_mb', 0),
            max_size_mb=rule_data.get('max_size_mb', 2000),
            filename_include=rule_data.get('filename_include'),
            filename_exclude=rule_data.get('filename_exclude'),
            file_extensions=rule_data.get('file_extensions'),
            
            # 发送者过滤
            enable_sender_filter=rule_data.get('enable_sender_filter', False),
            sender_filter_mode=rule_data.get('sender_filter_mode', 'whitelist'),
            sender_whitelist=rule_data.get('sender_whitelist'),
            sender_blacklist=rule_data.get('sender_blacklist'),
            
            # 下载设置
            temp_folder=rule_data.get('temp_folder', '/app/media/downloads'),
            concurrent_downloads=rule_data.get('concurrent_downloads', 3),
            retry_on_failure=rule_data.get('retry_on_failure', True),
            max_retries=rule_data.get('max_retries', 3),
            
            # 元数据提取
            extract_metadata=rule_data.get('extract_metadata', True),
            metadata_mode=rule_data.get('metadata_mode', 'lightweight'),
            metadata_timeout=rule_data.get('metadata_timeout', 10),
            async_metadata_extraction=rule_data.get('async_metadata_extraction', True),
            
            # 归档配置
            organize_enabled=rule_data.get('organize_enabled', False),
            organize_target_type=rule_data.get('organize_target_type', 'local'),
            organize_local_path=rule_data.get('organize_local_path'),
            organize_mode=rule_data.get('organize_mode', 'copy'),
            keep_temp_file=rule_data.get('keep_temp_file', False),
            
            # 文件夹结构
            folder_structure=rule_data.get('folder_structure', 'date'),
            custom_folder_template=rule_data.get('custom_folder_template'),
            rename_files=rule_data.get('rename_files', False),
            filename_template=rule_data.get('filename_template'),
            
            # 清理设置
            auto_cleanup_enabled=rule_data.get('auto_cleanup_enabled', True),
            auto_cleanup_days=rule_data.get('auto_cleanup_days', 7),
            cleanup_only_organized=rule_data.get('cleanup_only_organized', True),
            
            # 存储容量
            max_storage_gb=rule_data.get('max_storage_gb', 100)
        )
        
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        
        logger.info(f"创建监控规则成功: {rule.name} (ID: {rule.id})")
        
        # 通知客户端重新加载监听列表
        if rule.is_active:
            await notify_client_reload_chats(rule.client_id)
            
            # 通知媒体监控服务重新加载规则
            from services.media_monitor_service import get_media_monitor_service
            monitor_service = get_media_monitor_service()
            if monitor_service:
                await monitor_service.reload_rule(rule.id)
                logger.info(f"✅ 已通知媒体监控服务加载规则: {rule.name} (ID: {rule.id})")
        
        return {
            "success": True,
            "message": "创建成功",
            "rule": rule_to_dict(rule)
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"创建监控规则失败: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"创建失败: {str(e)}"}
        )


@router.put("/rules/{rule_id}")
async def update_monitor_rule(
    rule_id: int,
    rule_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新监控规则"""
    try:
        result = await db.execute(
            select(MediaMonitorRule).where(MediaMonitorRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "规则不存在"}
            )
        
        # 更新字段
        for key, value in rule_data.items():
            if key in ['source_chats', 'media_types', 'file_extensions'] and value is not None:
                # 只对列表/数组进行JSON编码，字符串直接使用（前端已编码）
                if isinstance(value, (list, tuple)):
                    value = json.dumps(value)
                # 如果已经是字符串，直接使用（前端已JSON.stringify）
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        rule.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(rule)
        
        logger.info(f"更新监控规则成功: {rule.name} (ID: {rule.id})")
        
        # 通知客户端重新加载监听列表
        await notify_client_reload_chats(rule.client_id)
        
        # 通知媒体监控服务重新加载规则
        from services.media_monitor_service import get_media_monitor_service
        monitor_service = get_media_monitor_service()
        if monitor_service:
            await monitor_service.reload_rule(rule.id)
            logger.info(f"✅ 已通知媒体监控服务重新加载规则: {rule.name} (ID: {rule.id})")
        
        return {
            "success": True,
            "message": "更新成功",
            "rule": rule_to_dict(rule)
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"更新监控规则失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"更新失败: {str(e)}"}
        )


@router.delete("/rules/{rule_id}")
async def delete_monitor_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除监控规则"""
    try:
        result = await db.execute(
            select(MediaMonitorRule).where(MediaMonitorRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "规则不存在"}
            )
        
        rule_name = rule.name
        client_id = rule.client_id
        
        await db.delete(rule)
        await db.commit()
        
        logger.info(f"删除监控规则成功: {rule_name} (ID: {rule_id})")
        
        # 通知客户端重新加载监听列表
        await notify_client_reload_chats(client_id)
        
        return {
            "success": True,
            "message": "删除成功"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"删除监控规则失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"删除失败: {str(e)}"}
        )


@router.post("/rules/{rule_id}/toggle")
async def toggle_monitor_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换监控规则启用/禁用状态"""
    try:
        result = await db.execute(
            select(MediaMonitorRule).where(MediaMonitorRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "规则不存在"}
            )
        
        rule.is_active = not rule.is_active
        rule.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(rule)
        
        logger.info(f"切换监控规则状态: {rule.name} -> {'启用' if rule.is_active else '禁用'}")
        
        # 通知客户端重新加载监听列表
        await notify_client_reload_chats(rule.client_id)
        
        return {
            "success": True,
            "message": f"规则已{'启用' if rule.is_active else '禁用'}",
            "is_active": rule.is_active
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"切换监控规则状态失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"切换失败: {str(e)}"}
        )


@router.get("/stats")
async def get_monitor_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取全局监控统计数据（用于仪表盘）"""
    try:
        # 总规则数
        total_rules = await db.scalar(select(func.count(MediaMonitorRule.id)))
        
        # 活跃规则数
        active_rules = await db.scalar(
            select(func.count(MediaMonitorRule.id)).where(MediaMonitorRule.is_active == True)
        )
        
        # 总下载数和总大小
        total_downloaded = await db.scalar(select(func.sum(MediaMonitorRule.total_downloaded))) or 0
        total_size_mb = await db.scalar(select(func.sum(MediaMonitorRule.total_size_mb))) or 0
        
        # 失败下载数
        total_failed = await db.scalar(select(func.sum(MediaMonitorRule.failed_downloads))) or 0
        
        return {
            "success": True,
            "stats": {
                "total_rules": total_rules or 0,
                "active_rules": active_rules or 0,
                "inactive_rules": (total_rules or 0) - (active_rules or 0),
                "total_downloaded": total_downloaded,
                "total_size_gb": round(total_size_mb / 1024, 2),
                "total_failed": total_failed,
                "success_rate": round((total_downloaded / (total_downloaded + total_failed) * 100), 2) if (total_downloaded + total_failed) > 0 else 100
            }
        }
        
    except Exception as e:
        logger.error(f"获取监控统计失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"获取统计失败: {str(e)}"}
        )


@router.get("/rules/{rule_id}/stats")
async def get_rule_stats(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个规则的统计数据"""
    try:
        result = await db.execute(
            select(MediaMonitorRule).where(MediaMonitorRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "规则不存在"}
            )
        
        # 计算成功率
        total_attempts = (rule.total_downloaded or 0) + (rule.failed_downloads or 0)
        success_rate = round((rule.total_downloaded / total_attempts * 100), 2) if total_attempts > 0 else 100
        
        return {
            "success": True,
            "stats": {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "is_active": rule.is_active,
                "total_downloaded": rule.total_downloaded or 0,
                "total_size_mb": rule.total_size_mb or 0,
                "total_size_gb": round((rule.total_size_mb or 0) / 1024, 2),
                "failed_downloads": rule.failed_downloads or 0,
                "success_rate": success_rate,
                "last_download_at": rule.last_download_at.isoformat() if rule.last_download_at else None,
                "created_at": rule.created_at.isoformat() if rule.created_at else None,
            }
        }
        
    except Exception as e:
        logger.error(f"获取规则统计失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"获取统计失败: {str(e)}"}
        )


# ==================== 辅助函数 ====================

def rule_to_dict(rule: MediaMonitorRule) -> dict:
    """将监控规则对象转换为字典"""
    
    # 辅助函数：处理可能的双重JSON编码
    def parse_json_field(field_value):
        if not field_value:
            return []
        # 如果已经是列表，直接返回
        if isinstance(field_value, list):
            return field_value
        # 如果是字符串，尝试解析
        if isinstance(field_value, str):
            parsed = json.loads(field_value)
            # 如果解析结果仍是字符串（双重编码），再解析一次
            if isinstance(parsed, str):
                parsed = json.loads(parsed)
            return parsed if isinstance(parsed, list) else []
        return []
    
    return {
        "id": rule.id,
        "name": rule.name,
        "description": rule.description,
        "is_active": rule.is_active,
        "client_id": rule.client_id,
        
        # 监听源
        "source_chats": parse_json_field(rule.source_chats),
        
        # 媒体过滤
        "media_types": parse_json_field(rule.media_types),
        "min_size_mb": rule.min_size_mb,
        "max_size_mb": rule.max_size_mb,
        "filename_include": rule.filename_include,
        "filename_exclude": rule.filename_exclude,
        "file_extensions": parse_json_field(rule.file_extensions),
        
        # 发送者过滤
        "enable_sender_filter": rule.enable_sender_filter,
        "sender_filter_mode": rule.sender_filter_mode,
        "sender_whitelist": rule.sender_whitelist,
        "sender_blacklist": rule.sender_blacklist,
        
        # 下载设置
        "temp_folder": rule.temp_folder,
        "concurrent_downloads": rule.concurrent_downloads,
        "retry_on_failure": rule.retry_on_failure,
        "max_retries": rule.max_retries,
        
        # 元数据提取
        "extract_metadata": rule.extract_metadata,
        "metadata_mode": rule.metadata_mode,
        "metadata_timeout": rule.metadata_timeout,
        "async_metadata_extraction": rule.async_metadata_extraction,
        
        # 归档配置
        "organize_enabled": rule.organize_enabled,
        "organize_target_type": rule.organize_target_type,
        "organize_local_path": rule.organize_local_path,
        "organize_mode": rule.organize_mode,
        "keep_temp_file": rule.keep_temp_file,
        
        # 文件夹结构
        "folder_structure": rule.folder_structure,
        "custom_folder_template": rule.custom_folder_template,
        "rename_files": rule.rename_files,
        "filename_template": rule.filename_template,
        
        # 清理设置
        "auto_cleanup_enabled": rule.auto_cleanup_enabled,
        "auto_cleanup_days": rule.auto_cleanup_days,
        "cleanup_only_organized": rule.cleanup_only_organized,
        
        # 存储容量
        "max_storage_gb": rule.max_storage_gb,
        
        # 统计数据
        "total_downloaded": rule.total_downloaded,
        "total_size_mb": rule.total_size_mb,
        "total_size_gb": round(rule.total_size_mb / 1024, 2) if rule.total_size_mb else 0,
        "last_download_at": rule.last_download_at.isoformat() if rule.last_download_at else None,
        "failed_downloads": rule.failed_downloads,
        
        # 时间戳
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
    }

