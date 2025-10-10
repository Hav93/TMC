"""Add last_connected to telegram_clients

Revision ID: 20250108_add_last_connected
Revises: 20250108_add_media_management
Create Date: 2025-10-08 19:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250108_add_last_connected'
down_revision = '20250108_add_media_management'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加 last_connected 字段"""
    with op.batch_alter_table('telegram_clients', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_connected', sa.DateTime(), nullable=True, comment='最后连接时间'))


def downgrade() -> None:
    """移除 last_connected 字段"""
    with op.batch_alter_table('telegram_clients', schema=None) as batch_op:
        batch_op.drop_column('last_connected')

