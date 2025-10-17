"""add pan115_use_proxy field

Revision ID: 20251017_add_pan115_use_proxy
Revises: 20251017_add_token_timestamps
Create Date: 2025-10-17 21:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251017_add_pan115_use_proxy'
down_revision = '20251017_add_token_timestamps'
branch_labels = None
depends_on = None


def upgrade():
    """添加pan115_use_proxy字段"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('media_settings')]
    
    with op.batch_alter_table('media_settings', schema=None) as batch_op:
        if 'pan115_use_proxy' not in columns:
            batch_op.add_column(sa.Column('pan115_use_proxy', sa.Boolean(), nullable=True, server_default='0', comment='115网盘API是否使用代理'))


def downgrade():
    """移除pan115_use_proxy字段"""
    with op.batch_alter_table('media_settings', schema=None) as batch_op:
        batch_op.drop_column('pan115_use_proxy')

