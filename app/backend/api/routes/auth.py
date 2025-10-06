"""
认证相关API路由 - 登录、注册、登出
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from database import get_db
from models import User, get_local_now
from auth import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["认证"])

# Pydantic 模型
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInfo(BaseModel):
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    avatar: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]


class UpdateProfile(BaseModel):
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    avatar: Optional[str] = Field(None, max_length=500, description="头像URL或Base64")


class ChangePassword(BaseModel):
    old_password: str = Field(..., min_length=6, description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


@router.post("/register", response_model=UserInfo, summary="创建新用户")
async def register(
    user_data: UserRegister, 
    db: AsyncSession = Depends(get_db)
):
    """
    创建新用户
    
    - 如果系统中没有任何用户，可以直接注册（第一个用户自动成为管理员）
    - 如果已有用户，则需要管理员权限才能创建新用户
    """
    # 检查是否有现有用户
    result = await db.execute(select(User))
    existing_users = result.scalars().all()
    
    # 如果已有用户，检查权限
    if existing_users:
        # 这是一个内部端点，调用者需要提供有效token
        # 由于我们需要保护这个端点，让它返回401，要求先登录
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User registration is disabled. Please contact an administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # 检查邮箱是否已存在
    if user_data.email:
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # 创建新用户
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=get_password_hash(user_data.password),
        is_admin=True  # 第一个用户自动成为管理员
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token, summary="用户登录")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    # 查找用户
    result = await db.execute(select(User).where(User.username == user_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # 更新最后登录时间
    user.last_login = get_local_now()
    await db.commit()
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前登录用户的信息"""
    return current_user


@router.post("/logout", summary="用户登出")
async def logout(current_user: User = Depends(get_current_active_user)):
    """用户登出（前端需删除token）"""
    return {"message": "Successfully logged out"}


@router.put("/profile", response_model=UserInfo, summary="更新个人信息")
async def update_profile(
    profile_data: UpdateProfile,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新个人信息（邮箱、全名、头像）
    """
    try:
        # 更新邮箱
        if profile_data.email is not None:
            # 检查邮箱是否已被其他用户使用
            if profile_data.email != current_user.email:
                result = await db.execute(select(User).where(User.email == profile_data.email))
                existing_user = result.scalar_one_or_none()
                if existing_user and existing_user.id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already in use by another user"
                    )
            current_user.email = profile_data.email
        
        # 更新全名
        if profile_data.full_name is not None:
            current_user.full_name = profile_data.full_name
        
        # 更新头像
        if profile_data.avatar is not None:
            current_user.avatar = profile_data.avatar
        
        # 保存更改
        await db.commit()
        await db.refresh(current_user)
        
        return current_user
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.post("/change-password", summary="修改密码")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改密码
    """
    try:
        # 验证旧密码
        if not current_user.check_password(password_data.old_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password is incorrect"
            )
        
        # 设置新密码
        current_user.set_password(password_data.new_password)
        
        # 保存更改
        await db.commit()
        
        return {"message": "Password changed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )

