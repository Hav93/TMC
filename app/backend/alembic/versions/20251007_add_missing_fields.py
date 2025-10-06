"""Add missing fields to telegram_clients and forward_rules

Revision ID: 20251007_add_missing_fields
Revises: 20251006_add_users
Create Date: 2025-10-07 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251007_add_missing_fields'
down_revision = '20251006_add_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加缺失的字段"""
    
    # 检查并添加 telegram_clients.admin_user_id
    with op.batch_alter_table('telegram_clients') as batch_op:
        try:
            batch_op.add_column(sa.Column('admin_user_id', sa.String(length=50), nullable=True, comment='管理员用户ID'))
        except Exception:
            pass  # 字段已存在
    
    # 检查并添加 forward_rules.client_id
    with op.batch_alter_table('forward_rules') as batch_op:
        try:
            batch_op.add_column(sa.Column('client_id', sa.String(length=100), nullable=True, comment='关联的客户端ID'))
        except Exception:
            pass  # 字段已存在
        
        try:
            batch_op.add_column(sa.Column('client_type', sa.String(length=20), nullable=True, comment='客户端类型'))
        except Exception:
            pass  # 字段已存在


def downgrade() -> None:
    """回滚：删除添加的字段"""
    
    with op.batch_alter_table('forward_rules') as batch_op:
        try:
            batch_op.drop_column('client_type')
        except Exception:
            pass
        
        try:
            batch_op.drop_column('client_id')
        except Exception:
            pass
    
    with op.batch_alter_table('telegram_clients') as batch_op:
        try:
            batch_op.drop_column('admin_user_id')
        except Exception:
            pass

