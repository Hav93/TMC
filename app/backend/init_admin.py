#!/usr/bin/env python3
"""
初始化管理员用户脚本
用于创建默认管理员账户
"""
import asyncio
from sqlalchemy import select
from database import db_manager
from models import User
from auth import get_password_hash
from log_manager import get_logger

logger = get_logger('init_admin', 'init_admin.log')

async def create_admin_user(
    username: str = "admin",
    password: str = "admin123",
    email: str = None,
    full_name: str = None
):
    """
    创建管理员用户
    
    Args:
        username: 用户名（默认：admin）
        password: 密码（默认：admin123）
        email: 邮箱（可选）
        full_name: 全名（可选）
    """
    # 确保数据库已初始化
    if not db_manager.async_session:
        await db_manager.init_db()
    
    async with db_manager.async_session() as db:
        try:
            # 检查用户是否已存在
            result = await db.execute(select(User).where(User.username == username))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.warning(f"⚠️  用户 '{username}' 已存在，跳过创建")
                print(f"⚠️  用户 '{username}' 已存在")
                return False
            
            # 创建新管理员用户
            admin_user = User(
                username=username,
                email=email,
                full_name=full_name,
                password_hash=get_password_hash(password),
                is_active=True,
                is_admin=True
            )
            
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
            
            logger.info(f"✅ 管理员用户创建成功！")
            logger.info(f"   用户名: {username}")
            logger.info(f"   密码: {password}")
            if email:
                logger.info(f"   邮箱: {email}")
            if full_name:
                logger.info(f"   姓名: {full_name}")
            
            print("=" * 60)
            print("✅ 管理员用户创建成功！")
            print("=" * 60)
            print(f"📝 用户名: {username}")
            print(f"🔑 密码: {password}")
            if email:
                print(f"📧 邮箱: {email}")
            if full_name:
                print(f"👤 姓名: {full_name}")
            print("=" * 60)
            print("⚠️  请在首次登录后立即修改密码！")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建管理员用户失败: {e}")
            print(f"❌ 创建管理员用户失败: {e}")
            await db.rollback()
            return False


async def main():
    """主函数"""
    print("🚀 开始初始化管理员用户...")
    
    # 使用默认值创建管理员
    success = await create_admin_user()
    
    if success:
        print("\n✅ 初始化完成！您现在可以使用以下凭据登录：")
        print("   http://localhost:9393/login")
        print("   用户名: admin")
        print("   密码: admin123")
    else:
        print("\n⚠️  初始化未完成，可能用户已存在")


if __name__ == "__main__":
    asyncio.run(main())

