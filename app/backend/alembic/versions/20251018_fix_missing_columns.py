"""fix missing columns in keywords and message_logs

Revision ID: 20251018_fix_missing_columns
Revises: 20251017_add_pan115_use_proxy
Create Date: 2025-10-18 09:15:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251018_fix_missing_columns'
down_revision = '20251017_add_pan115_use_proxy'
branch_labels = None
depends_on = None


def upgrade():
    """添加缺失的列并重命名现有列"""
    
    # 检查列是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # 1. 修复 keywords 表
    keywords_columns = [col['name'] for col in inspector.get_columns('keywords')]
    
    with op.batch_alter_table('keywords', schema=None) as batch_op:
        # 添加缺失的列
        if 'is_exclude' not in keywords_columns:
            batch_op.add_column(sa.Column('is_exclude', sa.Boolean(), nullable=True, server_default='0', comment='是否为排除关键词'))
        if 'case_sensitive' not in keywords_columns:
            batch_op.add_column(sa.Column('case_sensitive', sa.Boolean(), nullable=True, server_default='0', comment='是否区分大小写'))
    
    # 2. 修复 message_logs 表
    message_logs_columns = [col['name'] for col in inspector.get_columns('message_logs')]
    
    with op.batch_alter_table('message_logs', schema=None) as batch_op:
        # 如果存在旧字段名，重命名它们
        if 'original_message_id' in message_logs_columns and 'source_message_id' not in message_logs_columns:
            batch_op.alter_column('original_message_id', new_column_name='source_message_id')
        elif 'source_message_id' not in message_logs_columns:
            # 如果两个都不存在，创建新字段
            batch_op.add_column(sa.Column('source_message_id', sa.Integer(), nullable=True, comment='源消息ID'))
        
        if 'forwarded_message_id' in message_logs_columns and 'target_message_id' not in message_logs_columns:
            batch_op.alter_column('forwarded_message_id', new_column_name='target_message_id')
        elif 'target_message_id' not in message_logs_columns:
            # 如果两个都不存在，创建新字段
            batch_op.add_column(sa.Column('target_message_id', sa.Integer(), nullable=True, comment='目标消息ID'))
        
        # 添加其他可能缺失的字段
        if 'media_type' not in message_logs_columns:
            batch_op.add_column(sa.Column('media_type', sa.String(50), nullable=True, comment='媒体类型'))
        if 'content_hash' not in message_logs_columns:
            batch_op.add_column(sa.Column('content_hash', sa.String(64), nullable=True, comment='内容哈希'))
        if 'media_hash' not in message_logs_columns:
            batch_op.add_column(sa.Column('media_hash', sa.String(64), nullable=True, comment='媒体哈希'))
        if 'sender_id' not in message_logs_columns:
            batch_op.add_column(sa.Column('sender_id', sa.String(50), nullable=True, comment='发送者ID'))
        if 'sender_username' not in message_logs_columns:
            batch_op.add_column(sa.Column('sender_username', sa.String(100), nullable=True, comment='发送者用户名'))
        if 'status' not in message_logs_columns:
            batch_op.add_column(sa.Column('status', sa.String(20), nullable=True, server_default='success', comment='处理状态'))
        if 'error_message' not in message_logs_columns:
            batch_op.add_column(sa.Column('error_message', sa.Text(), nullable=True, comment='错误消息'))
        if 'processing_time' not in message_logs_columns:
            batch_op.add_column(sa.Column('processing_time', sa.Float(), nullable=True, comment='处理时间(秒)'))
    
    # 3. 修复 replace_rules 表（添加缺失字段）
    replace_rules_columns = [col['name'] for col in inspector.get_columns('replace_rules')]
    
    with op.batch_alter_table('replace_rules', schema=None) as batch_op:
        if 'name' not in replace_rules_columns:
            batch_op.add_column(sa.Column('name', sa.String(100), nullable=True, comment='替换规则名称'))
        if 'is_active' not in replace_rules_columns:
            batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1', comment='是否启用'))
        if 'is_global' not in replace_rules_columns:
            batch_op.add_column(sa.Column('is_global', sa.Boolean(), nullable=True, server_default='0', comment='是否为全局规则'))


def downgrade():
    """回滚更改"""
    
    # 回滚 keywords 表
    with op.batch_alter_table('keywords', schema=None) as batch_op:
        batch_op.drop_column('case_sensitive')
        batch_op.drop_column('is_exclude')
    
    # 回滚 message_logs 表
    with op.batch_alter_table('message_logs', schema=None) as batch_op:
        batch_op.alter_column('source_message_id', new_column_name='original_message_id')
        batch_op.alter_column('target_message_id', new_column_name='forwarded_message_id')
        batch_op.drop_column('processing_time')
        batch_op.drop_column('error_message')
        batch_op.drop_column('status')
        batch_op.drop_column('sender_username')
        batch_op.drop_column('sender_id')
        batch_op.drop_column('media_hash')
        batch_op.drop_column('content_hash')
        batch_op.drop_column('media_type')
    
    # 回滚 replace_rules 表
    with op.batch_alter_table('replace_rules', schema=None) as batch_op:
        batch_op.drop_column('is_global')
        batch_op.drop_column('is_active')
        batch_op.drop_column('name')

