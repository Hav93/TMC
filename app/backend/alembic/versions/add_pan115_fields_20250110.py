"""add pan115 fields to media_settings

Revision ID: add_pan115_fields_20250110
Revises: add_bot_settings_user_sessions_20251009
Create Date: 2025-01-10 20:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_pan115_fields_20250110'
down_revision = 'add_bot_settings_user_sessions_20251009'
branch_labels = None
depends_on = None


def upgrade():
    """添加115网盘配置字段到media_settings表"""
    from sqlalchemy import inspect
    from sqlalchemy.engine import reflection
    
    # 获取数据库连接
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # 获取现有列名
    existing_columns = [col['name'] for col in inspector.get_columns('media_settings')]
    
    # 只添加不存在的列
    if 'pan115_app_id' not in existing_columns:
        op.add_column('media_settings', sa.Column('pan115_app_id', sa.String(50), comment='115开放平台AppID'))
    if 'pan115_user_id' not in existing_columns:
        op.add_column('media_settings', sa.Column('pan115_user_id', sa.String(100), comment='115用户ID'))
    if 'pan115_user_key' not in existing_columns:
        op.add_column('media_settings', sa.Column('pan115_user_key', sa.String(200), comment='115用户密钥'))
    if 'pan115_request_interval' not in existing_columns:
        op.add_column('media_settings', sa.Column('pan115_request_interval', sa.Float(), server_default='1.0', comment='API请求间隔(秒)'))


def downgrade():
    """回滚115网盘配置字段"""
    op.drop_column('media_settings', 'pan115_request_interval')
    op.drop_column('media_settings', 'pan115_user_key')
    op.drop_column('media_settings', 'pan115_user_id')
    op.drop_column('media_settings', 'pan115_app_id')

