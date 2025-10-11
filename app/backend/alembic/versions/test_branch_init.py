"""test分支初始数据库结构

Revision ID: test_branch_init
Revises: 
Create Date: 2025-10-11 15:05:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'test_branch_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建 test 分支的初始数据库结构"""
    
    # 使用 SQLAlchemy 的声明式模型自动创建所有表
    # 这样可以避免手动定义每个表的结构
    from sqlalchemy import create_engine
    from models import Base
    import os
    
    # 获取当前数据库 URL
    database_url = os.getenv('DATABASE_URL', 'sqlite:///data/bot.db')
    engine = create_engine(database_url)
    
    # 创建所有表
    Base.metadata.create_all(engine)


def downgrade() -> None:
    """删除所有表"""
    pass

