"""Add last_connected to telegram_clients

Revision ID: add_last_connected_20250108
Revises: add_media_management_20250108
Create Date: 2025-10-08 19:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_last_connected_20250108'
down_revision = 'add_media_management_20250108'
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

