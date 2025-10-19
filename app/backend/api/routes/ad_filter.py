"""
广告过滤API路由
"""
from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from api.dependencies import get_current_user
from services.ad_filter_service import get_ad_filter_service, AdFilterRule, FilterAction
from log_manager import get_logger

logger = get_logger('ad_filter_api', 'enhanced_bot.log')

router = APIRouter(tags=["广告过滤"])


class FileCheckRequest(BaseModel):
    """文件检查请求"""
    filename: str = Field(..., description="文件名")
    file_size: int = Field(None, description="文件大小（字节）")


class BatchCheckRequest(BaseModel):
    """批量检查请求"""
    files: List[Dict[str, Any]] = Field(..., description="文件列表")


class AddRuleRequest(BaseModel):
    """添加规则请求"""
    pattern: str = Field(..., description="文件名模式（正则）")
    min_size: int = Field(None, description="最小文件大小")
    max_size: int = Field(None, description="最大文件大小")
    action: str = Field("skip", description="过滤动作")
    description: str = Field("", description="规则描述")
    priority: int = Field(1, description="优先级")


@router.post("/check")
async def check_file(
    request: FileCheckRequest,
    current_user: Any = Depends(get_current_user)
):
    """检查单个文件是否为广告"""
    try:
        service = get_ad_filter_service()
        action, reason = service.check_file(request.filename, request.file_size)
        
        return {
            "success": True,
            "data": {
                "filename": request.filename,
                "is_ad": action != FilterAction.ALLOW,
                "action": action.value,
                "reason": reason
            }
        }
    except Exception as e:
        logger.error(f"检查文件失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.post("/batch-check")
async def batch_check_files(
    request: BatchCheckRequest,
    current_user: Any = Depends(get_current_user)
):
    """批量检查文件"""
    try:
        service = get_ad_filter_service()
        allowed, filtered = service.filter_files(request.files)
        
        return {
            "success": True,
            "data": {
                "total": len(request.files),
                "allowed": len(allowed),
                "filtered": len(filtered),
                "allowed_files": allowed,
                "filtered_files": filtered
            }
        }
    except Exception as e:
        logger.error(f"批量检查失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.get("/rules")
async def get_rules(current_user: Any = Depends(get_current_user)):
    """获取所有过滤规则"""
    try:
        service = get_ad_filter_service()
        rules = [
            {
                "pattern": rule.pattern,
                "min_size": rule.min_size,
                "max_size": rule.max_size,
                "action": rule.action.value,
                "description": rule.description,
                "priority": rule.priority
            }
            for rule in service.rules
        ]
        
        return {
            "success": True,
            "data": rules
        }
    except Exception as e:
        logger.error(f"获取规则失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.post("/rules")
async def add_rule(
    request: AddRuleRequest,
    current_user: Any = Depends(get_current_user)
):
    """添加自定义规则"""
    try:
        service = get_ad_filter_service()
        
        rule = AdFilterRule(
            pattern=request.pattern,
            min_size=request.min_size,
            max_size=request.max_size,
            action=FilterAction(request.action),
            description=request.description,
            priority=request.priority
        )
        
        service.add_rule(rule)
        
        return {
            "success": True,
            "message": "规则添加成功",
            "data": {
                "pattern": rule.pattern,
                "description": rule.description
            }
        }
    except Exception as e:
        logger.error(f"添加规则失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.get("/whitelist")
async def get_whitelist(current_user: Any = Depends(get_current_user)):
    """获取白名单"""
    try:
        service = get_ad_filter_service()
        return {
            "success": True,
            "data": service.whitelist_patterns
        }
    except Exception as e:
        logger.error(f"获取白名单失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.post("/whitelist")
async def add_whitelist(
    pattern: str,
    current_user: Any = Depends(get_current_user)
):
    """添加白名单模式"""
    try:
        service = get_ad_filter_service()
        service.add_whitelist(pattern)
        
        return {
            "success": True,
            "message": "白名单添加成功"
        }
    except Exception as e:
        logger.error(f"添加白名单失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@router.get("/stats")
async def get_stats(current_user: Any = Depends(get_current_user)):
    """获取统计信息"""
    try:
        service = get_ad_filter_service()
        stats = service.get_stats()
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取统计失败: {e}", exc_info=True)
        return {"success": False, "message": str(e)}

