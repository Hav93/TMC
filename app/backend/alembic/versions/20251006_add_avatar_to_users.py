"""add avatar to users

Revision ID: 20251006_add_avatar
Revises: 20251006_add_users
Create Date: 2025-10-06 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251006_add_avatar'
down_revision = '20251006_add_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加avatar字段到users表
    op.add_column('users', sa.Column('avatar', sa.String(length=500), nullable=True, comment='头像URL或Base64'))


def downgrade() -> None:
    # 删除avatar字段
    op.drop_column('users', 'avatar')

