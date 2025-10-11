"""add avatar to users

Revision ID: add_avatar_20251006
Revises: add_users_20251006
Create Date: 2025-10-06 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_avatar_20251006'
down_revision = 'add_users_20251006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加avatar字段到users表
    op.add_column('users', sa.Column('avatar', sa.String(length=500), nullable=True, comment='头像URL或Base64'))


def downgrade() -> None:
    # 删除avatar字段
    op.drop_column('users', 'avatar')

