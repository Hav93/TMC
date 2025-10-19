"""添加access_token和时间戳字段

Revision ID: 20251017_add_token_timestamps
Revises: 20251016_add_pan115_user_info
Create Date: 2025-10-17 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251017_add_token_timestamps'
down_revision = '20251016_add_pan115_user_info'
branch_labels = None
depends_on = None


def upgrade():
    """添加pan115_access_token、pan115_token_expires_at和pan115_last_refresh_at字段"""
    # 检查列是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('media_settings')]
    
    with op.batch_alter_table('media_settings', schema=None) as batch_op:
        # 只添加不存在的列
        if 'pan115_access_token' not in columns:
            batch_op.add_column(sa.Column('pan115_access_token', sa.Text(), nullable=True, comment='115开放平台access_token(扫码登录时获取)'))
        if 'pan115_token_expires_at' not in columns:
            batch_op.add_column(sa.Column('pan115_token_expires_at', sa.DateTime(), nullable=True, comment='access_token过期时间'))
        if 'pan115_last_refresh_at' not in columns:
            batch_op.add_column(sa.Column('pan115_last_refresh_at', sa.DateTime(), nullable=True, comment='最后刷新用户信息时间'))


def downgrade():
    """移除所有新增字段"""
    with op.batch_alter_table('media_settings', schema=None) as batch_op:
        batch_op.drop_column('pan115_last_refresh_at')
        batch_op.drop_column('pan115_token_expires_at')
        batch_op.drop_column('pan115_access_token')

