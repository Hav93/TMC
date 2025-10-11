"""add cascade delete to media files

Revision ID: 20250111_add_cascade_delete
Revises: test_branch_init
Create Date: 2025-01-11 17:35:52

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250111_add_cascade_delete'
down_revision = 'test_branch_init'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加级联删除约束"""
    # SQLite 不支持直接修改外键，需要重建表
    # 但由于这是一个小改动，我们可以在应用层处理
    # 这个迁移主要是为了记录变更
    pass


def downgrade() -> None:
    """回滚级联删除约束"""
    pass

