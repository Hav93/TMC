"""
用户管理路由
提供用户的CRUD操作（仅管理员可访问）
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from database import get_db
from models import User
from auth import get_current_user, get_password_hash
from log_manager import get_logger

router = APIRouter()
logger = get_logger('api_users', 'api.log')

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_admin: bool = False

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class UsersListResponse(BaseModel):
    total: int
    users: List[UserResponse]


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求当前用户必须是管理员"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access this resource"
        )
    return current_user


@router.get("", response_model=UsersListResponse, summary="获取用户列表")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有用户列表（仅管理员）
    """
    try:
        # 获取总数
        count_query = select(func.count()).select_from(User)
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 获取用户列表
        query = select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await db.execute(query)
        users = result.scalars().all()
        
        logger.info(f"👥 管理员 {current_user.username} 查询用户列表，返回 {len(users)} 条记录")
        
        return UsersListResponse(
            total=total,
            users=[UserResponse.from_orm(user) for user in users]
        )
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )


@router.post("", response_model=UserResponse, summary="创建新用户")
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新用户（仅管理员）
    """
    try:
        # 检查用户名是否已存在
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user_data.username}' already exists"
            )
        
        # 检查邮箱是否已存在
        if user_data.email:
            result = await db.execute(
                select(User).where(User.email == user_data.email)
            )
            existing_email = result.scalar_one_or_none()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{user_data.email}' already in use"
                )
        
        # 创建新用户
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            is_admin=user_data.is_admin,
            is_active=True
        )
        new_user.set_password(user_data.password)
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"✅ 管理员 {current_user.username} 创建新用户: {new_user.username} (管理员: {new_user.is_admin})")
        
        return UserResponse.from_orm(new_user)
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户的详细信息（仅管理员）
    """
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        return UserResponse.from_orm(user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户信息（仅管理员）
    """
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        # 不允许修改自己的管理员状态
        if user.id == current_user.id and user_data.is_admin is not None:
            if not user_data.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You cannot remove your own admin privileges"
                )
        
        # 检查邮箱是否被其他用户占用
        if user_data.email and user_data.email != user.email:
            result = await db.execute(
                select(User).where(User.email == user_data.email)
            )
            existing_email = result.scalar_one_or_none()
            if existing_email and existing_email.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{user_data.email}' already in use"
                )
        
        # 更新字段
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        if user_data.is_admin is not None:
            user.is_admin = user_data.is_admin
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"✅ 管理员 {current_user.username} 更新用户: {user.username}")
        
        return UserResponse.from_orm(user)
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    删除用户（仅管理员）
    """
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        # 不允许删除自己
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete your own account"
            )
        
        # 检查是否是最后一个管理员
        if user.is_admin:
            count_query = select(func.count()).select_from(User).where(User.is_admin == True)
            result = await db.execute(count_query)
            admin_count = result.scalar()
            
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last administrator account"
                )
        
        username = user.username
        await db.delete(user)
        await db.commit()
        
        logger.info(f"🗑️ 管理员 {current_user.username} 删除用户: {username}")
        
        return {"success": True, "message": f"User '{username}' deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/{user_id}/reset-password", summary="重置用户密码")
async def reset_password(
    user_id: int,
    new_password: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    重置用户密码（仅管理员）
    """
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
        
        user.set_password(new_password)
        await db.commit()
        
        logger.info(f"🔑 管理员 {current_user.username} 重置用户 {user.username} 的密码")
        
        return {"success": True, "message": f"Password for user '{user.username}' has been reset"}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"重置密码失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )

