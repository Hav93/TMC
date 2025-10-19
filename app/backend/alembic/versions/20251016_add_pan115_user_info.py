"""add pan115_user_info field

Revision ID: 20251016_add_pan115_user_info
Revises: 20250114_add_notification_system
Create Date: 2025-10-16 22:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251016_add_pan115_user_info'
down_revision = '20250114_add_notification_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 pan115_user_info 字段到 media_settings 表
    op.add_column('media_settings', sa.Column('pan115_user_info', sa.Text(), nullable=True, comment='115用户信息(JSON格式，包含用户名、VIP等级、空间信息等)'))


def downgrade() -> None:
    # 删除 pan115_user_info 字段
    op.drop_column('media_settings', 'pan115_user_info')

