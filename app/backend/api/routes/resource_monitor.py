"""
资源监控API路由
"""
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database import get_db
from models import ResourceMonitorRule, ResourceRecord
from services.resource_monitor_service import ResourceMonitorService

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Pydantic Models ====================

class ResourceMonitorRuleCreate(BaseModel):
    """创建资源监控规则"""
    name: str
    source_chats: List[int]
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    monitor_pan115: bool = True
    monitor_magnet: bool = True
    monitor_ed2k: bool = True
    target_path: str
    auto_save: bool = False


class ResourceMonitorRuleUpdate(BaseModel):
    """更新资源监控规则"""
    name: Optional[str] = None
    source_chats: Optional[List[int]] = None
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    monitor_pan115: Optional[bool] = None
    monitor_magnet: Optional[bool] = None
    monitor_ed2k: Optional[bool] = None
    target_path: Optional[str] = None
    auto_save: Optional[bool] = None
    is_active: Optional[bool] = None


class AddTagRequest(BaseModel):
    """添加标签请求"""
    tag: str


class BatchOperationRequest(BaseModel):
    """批量操作请求"""
    record_ids: List[int]
    action: str  # 'save', 'delete', 'ignore'


# ==================== 规则管理 ====================

@router.get("/rules")
async def list_rules(
    db: AsyncSession = Depends(get_db)
):
    """获取所有监控规则"""
    try:
        query = select(ResourceMonitorRule).order_by(desc(ResourceMonitorRule.created_at))
        result = await db.execute(query)
        rules = result.scalars().all()
        
        # 转换为字典
        rules_data = []
        for rule in rules:
            rule_dict = {
                'id': rule.id,
                'name': rule.name,
                'source_chats': json.loads(rule.source_chats) if rule.source_chats else [],
                'include_keywords': json.loads(rule.include_keywords) if rule.include_keywords else [],
                'exclude_keywords': json.loads(rule.exclude_keywords) if rule.exclude_keywords else [],
                'monitor_pan115': rule.monitor_pan115,
                'monitor_magnet': rule.monitor_magnet,
                'monitor_ed2k': rule.monitor_ed2k,
                'target_path': rule.target_path,
                'auto_save': rule.auto_save,
                'is_active': rule.is_active,
                'total_captured': rule.total_captured or 0,
                'total_saved': rule.total_saved or 0,
                'created_at': rule.created_at.isoformat() if rule.created_at else None,
                'updated_at': rule.updated_at.isoformat() if rule.updated_at else None,
            }
            rules_data.append(rule_dict)
        
        return JSONResponse(content={
            'success': True,
            'rules': rules_data
        })
    
    except Exception as e:
        logger.error(f"获取规则列表失败: {e}")
        return JSONResponse(content={
            'success': False,
            'message': f'获取规则列表失败: {str(e)}'
        }, status_code=500)


@router.post("/rules")
async def create_rule(
    rule_data: ResourceMonitorRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建监控规则"""
    try:
        rule = ResourceMonitorRule(
            name=rule_data.name,
            source_chats=json.dumps(rule_data.source_chats),
            include_keywords=json.dumps(rule_data.include_keywords) if rule_data.include_keywords else None,
            exclude_keywords=json.dumps(rule_data.exclude_keywords) if rule_data.exclude_keywords else None,
            monitor_pan115=rule_data.monitor_pan115,
            monitor_magnet=rule_data.monitor_magnet,
            monitor_ed2k=rule_data.monitor_ed2k,
            target_path=rule_data.target_path,
            auto_save=rule_data.auto_save,
            is_active=True,
            total_captured=0,
            total_saved=0
        )
        
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        
        logger.info(f"✅ 创建监控规则成功: {rule.name}")
        
        return JSONResponse(content={
            'success': True,
            'message': '规则创建成功',
            'rule_id': rule.id
        })
    
    except Exception as e:
        logger.error(f"创建规则失败: {e}")
        await db.rollback()
        return JSONResponse(content={
            'success': False,
            'message': f'创建规则失败: {str(e)}'
        }, status_code=500)


@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    rule_data: ResourceMonitorRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新监控规则"""
    try:
        result = await db.execute(
            select(ResourceMonitorRule).where(ResourceMonitorRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            return JSONResponse(content={
                'success': False,
                'message': '规则不存在'
            }, status_code=404)
        
        # 更新字段
        if rule_data.name is not None:
            rule.name = rule_data.name
        if rule_data.source_chats is not None:
            rule.source_chats = json.dumps(rule_data.source_chats)
        if rule_data.include_keywords is not None:
            rule.include_keywords = json.dumps(rule_data.include_keywords)
        if rule_data.exclude_keywords is not None:
            rule.exclude_keywords = json.dumps(rule_data.exclude_keywords)
        if rule_data.monitor_pan115 is not None:
            rule.monitor_pan115 = rule_data.monitor_pan115
        if rule_data.monitor_magnet is not None:
            rule.monitor_magnet = rule_data.monitor_magnet
        if rule_data.monitor_ed2k is not None:
            rule.monitor_ed2k = rule_data.monitor_ed2k
        if rule_data.target_path is not None:
            rule.target_path = rule_data.target_path
        if rule_data.auto_save is not None:
            rule.auto_save = rule_data.auto_save
        if rule_data.is_active is not None:
            rule.is_active = rule_data.is_active
        
        await db.commit()
        
        logger.info(f"✅ 更新监控规则成功: {rule.name}")
        
        return JSONResponse(content={
            'success': True,
            'message': '规则更新成功'
        })
    
    except Exception as e:
        logger.error(f"更新规则失败: {e}")
        await db.rollback()
        return JSONResponse(content={
            'success': False,
            'message': f'更新规则失败: {str(e)}'
        }, status_code=500)


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除监控规则"""
    try:
        result = await db.execute(
            select(ResourceMonitorRule).where(ResourceMonitorRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            return JSONResponse(content={
                'success': False,
                'message': '规则不存在'
            }, status_code=404)
        
        await db.delete(rule)
        await db.commit()
        
        logger.info(f"✅ 删除监控规则成功: {rule.name}")
        
        return JSONResponse(content={
            'success': True,
            'message': '规则删除成功'
        })
    
    except Exception as e:
        logger.error(f"删除规则失败: {e}")
        await db.rollback()
        return JSONResponse(content={
            'success': False,
            'message': f'删除规则失败: {str(e)}'
        }, status_code=500)


# ==================== 资源记录管理 ====================

@router.get("/records")
async def list_records(
    rule_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取资源记录列表"""
    try:
        query = select(ResourceRecord)
        
        # 过滤条件
        if rule_id:
            query = query.where(ResourceRecord.rule_id == rule_id)
        if status:
            query = query.where(ResourceRecord.status == status)
        if search:
            query = query.where(
                or_(
                    ResourceRecord.message_text.contains(search),
                    ResourceRecord.chat_title.contains(search)
                )
            )
        
        # 标签过滤
        if tags:
            tag_list = tags.split(',')
            # TODO: 实现标签过滤（需要JSON查询）
        
        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        query = query.order_by(desc(ResourceRecord.detected_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        records = result.scalars().all()
        
        # 转换为字典
        records_data = []
        for record in records:
            record_dict = {
                'id': record.id,
                'rule_id': record.rule_id,
                'rule_name': record.rule.name if record.rule else '',
                'message_text': record.message_text,
                'chat_id': record.chat_id,
                'chat_title': record.chat_title,
                'message_id': record.message_id,
                'sender_name': record.sender_name,
                'pan115_links': json.loads(record.pan115_links) if record.pan115_links else [],
                'magnet_links': json.loads(record.magnet_links) if record.magnet_links else [],
                'ed2k_links': json.loads(record.ed2k_links) if record.ed2k_links else [],
                'tags': json.loads(record.tags) if record.tags else [],
                'status': record.status,
                'target_path': record.target_path,
                'error_message': record.error_message,
                'detected_at': record.detected_at.isoformat() if record.detected_at else None,
                'saved_at': record.saved_at.isoformat() if record.saved_at else None,
            }
            records_data.append(record_dict)
        
        return JSONResponse(content={
            'success': True,
            'records': records_data,
            'total': total,
            'page': page,
            'page_size': page_size
        })
    
    except Exception as e:
        logger.error(f"获取记录列表失败: {e}")
        return JSONResponse(content={
            'success': False,
            'message': f'获取记录列表失败: {str(e)}'
        }, status_code=500)


@router.get("/records/{record_id}")
async def get_record_detail(
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
            return JSONResponse(content={
                'success': False,
                'message': '记录不存在'
            }, status_code=404)
        
        # 解析消息快照
        snapshot = json.loads(record.message_snapshot) if record.message_snapshot else {}
        
        record_dict = {
            'id': record.id,
            'rule_id': record.rule_id,
            'rule_name': record.rule.name if record.rule else '',
            'message_text': record.message_text,
            'message_snapshot': snapshot,
            'chat_id': record.chat_id,
            'chat_title': record.chat_title,
            'message_id': record.message_id,
            'sender_name': record.sender_name,
            'pan115_links': json.loads(record.pan115_links) if record.pan115_links else [],
            'magnet_links': json.loads(record.magnet_links) if record.magnet_links else [],
            'ed2k_links': json.loads(record.ed2k_links) if record.ed2k_links else [],
            'tags': json.loads(record.tags) if record.tags else [],
            'status': record.status,
            'target_path': record.target_path,
            'error_message': record.error_message,
            'detected_at': record.detected_at.isoformat() if record.detected_at else None,
            'saved_at': record.saved_at.isoformat() if record.saved_at else None,
        }
        
        return JSONResponse(content={
            'success': True,
            'record': record_dict
        })
    
    except Exception as e:
        logger.error(f"获取记录详情失败: {e}")
        return JSONResponse(content={
            'success': False,
            'message': f'获取记录详情失败: {str(e)}'
        }, status_code=500)


# ==================== 标签管理 ====================

@router.post("/records/{record_id}/tags")
async def add_tag(
    record_id: int,
    tag_data: AddTagRequest,
    db: AsyncSession = Depends(get_db)
):
    """添加标签"""
    try:
        result = await db.execute(
            select(ResourceRecord).where(ResourceRecord.id == record_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            return JSONResponse(content={
                'success': False,
                'message': '记录不存在'
            }, status_code=404)
        
        # 解析现有标签
        tags = json.loads(record.tags) if record.tags else []
        
        # 添加新标签
        if tag_data.tag not in tags:
            tags.append(tag_data.tag)
            record.tags = json.dumps(tags, ensure_ascii=False)
            await db.commit()
        
        return JSONResponse(content={
            'success': True,
            'message': '标签添加成功',
            'tags': tags
        })
    
    except Exception as e:
        logger.error(f"添加标签失败: {e}")
        await db.rollback()
        return JSONResponse(content={
            'success': False,
            'message': f'添加标签失败: {str(e)}'
        }, status_code=500)


@router.delete("/records/{record_id}/tags/{tag}")
async def remove_tag(
    record_id: int,
    tag: str,
    db: AsyncSession = Depends(get_db)
):
    """删除标签"""
    try:
        result = await db.execute(
            select(ResourceRecord).where(ResourceRecord.id == record_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            return JSONResponse(content={
                'success': False,
                'message': '记录不存在'
            }, status_code=404)
        
        # 解析现有标签
        tags = json.loads(record.tags) if record.tags else []
        
        # 删除标签
        if tag in tags:
            tags.remove(tag)
            record.tags = json.dumps(tags, ensure_ascii=False)
            await db.commit()
        
        return JSONResponse(content={
            'success': True,
            'message': '标签删除成功',
            'tags': tags
        })
    
    except Exception as e:
        logger.error(f"删除标签失败: {e}")
        await db.rollback()
        return JSONResponse(content={
            'success': False,
            'message': f'删除标签失败: {str(e)}'
        }, status_code=500)


# ==================== 批量操作 ====================

@router.post("/records/batch")
async def batch_operation(
    operation: BatchOperationRequest,
    db: AsyncSession = Depends(get_db)
):
    """批量操作"""
    try:
        if operation.action == 'delete':
            # 批量删除
            for record_id in operation.record_ids:
                result = await db.execute(
                    select(ResourceRecord).where(ResourceRecord.id == record_id)
                )
                record = result.scalar_one_or_none()
                if record:
                    await db.delete(record)
            
            await db.commit()
            
            return JSONResponse(content={
                'success': True,
                'message': f'成功删除 {len(operation.record_ids)} 条记录'
            })
        
        elif operation.action == 'ignore':
            # 批量忽略
            for record_id in operation.record_ids:
                result = await db.execute(
                    select(ResourceRecord).where(ResourceRecord.id == record_id)
                )
                record = result.scalar_one_or_none()
                if record:
                    record.status = 'ignored'
            
            await db.commit()
            
            return JSONResponse(content={
                'success': True,
                'message': f'成功忽略 {len(operation.record_ids)} 条记录'
            })
        
        elif operation.action == 'save':
            # 批量转存
            service = ResourceMonitorService(db)
            success_count = 0
            
            for record_id in operation.record_ids:
                result = await db.execute(
                    select(ResourceRecord).where(ResourceRecord.id == record_id)
                )
                record = result.scalar_one_or_none()
                if record and record.status == 'pending':
                    await service.auto_save_to_115(record)
                    success_count += 1
            
            return JSONResponse(content={
                'success': True,
                'message': f'成功处理 {success_count} 条记录'
            })
        
        else:
            return JSONResponse(content={
                'success': False,
                'message': '不支持的操作类型'
            }, status_code=400)
    
    except Exception as e:
        logger.error(f"批量操作失败: {e}")
        await db.rollback()
        return JSONResponse(content={
            'success': False,
            'message': f'批量操作失败: {str(e)}'
        }, status_code=500)

