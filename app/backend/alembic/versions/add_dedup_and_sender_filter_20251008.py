"""add dedup and sender filter

Revision ID: add_dedup_and_sender_filter_20251008
Revises: add_missing_fields_20251007
Create Date: 2025-10-08 14:04:19

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_dedup_and_sender_filter_20251008'
down_revision = 'add_missing_fields_20251007'
branch_labels = None
depends_on = None

def upgrade():
    # 在 forward_rules 表添加消息去重字段
    with op.batch_alter_table('forward_rules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('enable_deduplication', sa.Boolean(), nullable=True, comment='是否启用消息去重'))
        batch_op.add_column(sa.Column('dedup_time_window', sa.Integer(), nullable=True, comment='去重时间窗口(秒)，默认1小时'))
        batch_op.add_column(sa.Column('dedup_check_content', sa.Boolean(), nullable=True, comment='去重时检查消息内容'))
        batch_op.add_column(sa.Column('dedup_check_media', sa.Boolean(), nullable=True, comment='去重时检查媒体文件'))
        
        # 添加发送者过滤字段
        batch_op.add_column(sa.Column('enable_sender_filter', sa.Boolean(), nullable=True, comment='是否启用发送者过滤'))
        batch_op.add_column(sa.Column('sender_filter_mode', sa.String(20), nullable=True, comment='发送者过滤模式'))
        batch_op.add_column(sa.Column('sender_whitelist', sa.Text(), nullable=True, comment='发送者白名单'))
        batch_op.add_column(sa.Column('sender_blacklist', sa.Text(), nullable=True, comment='发送者黑名单'))
    
    # 在 message_logs 表添加消息指纹字段
    with op.batch_alter_table('message_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('content_hash', sa.String(64), nullable=True, comment='消息内容哈希值'))
        batch_op.add_column(sa.Column('media_hash', sa.String(64), nullable=True, comment='媒体文件哈希值'))
        batch_op.add_column(sa.Column('sender_id', sa.String(50), nullable=True, comment='发送者ID'))
        batch_op.add_column(sa.Column('sender_username', sa.String(100), nullable=True, comment='发送者用户名'))
        batch_op.create_index('ix_message_logs_content_hash', ['content_hash'])
    
    # 设置默认值
    op.execute("UPDATE forward_rules SET enable_deduplication = 0 WHERE enable_deduplication IS NULL")
    op.execute("UPDATE forward_rules SET dedup_time_window = 3600 WHERE dedup_time_window IS NULL")
    op.execute("UPDATE forward_rules SET dedup_check_content = 1 WHERE dedup_check_content IS NULL")
    op.execute("UPDATE forward_rules SET dedup_check_media = 1 WHERE dedup_check_media IS NULL")
    op.execute("UPDATE forward_rules SET enable_sender_filter = 0 WHERE enable_sender_filter IS NULL")
    op.execute("UPDATE forward_rules SET sender_filter_mode = 'whitelist' WHERE sender_filter_mode IS NULL")

def downgrade():
    # 移除 message_logs 表的字段
    with op.batch_alter_table('message_logs', schema=None) as batch_op:
        batch_op.drop_index('ix_message_logs_content_hash')
        batch_op.drop_column('sender_username')
        batch_op.drop_column('sender_id')
        batch_op.drop_column('media_hash')
        batch_op.drop_column('content_hash')
    
    # 移除 forward_rules 表的字段
    with op.batch_alter_table('forward_rules', schema=None) as batch_op:
        batch_op.drop_column('sender_blacklist')
        batch_op.drop_column('sender_whitelist')
        batch_op.drop_column('sender_filter_mode')
        batch_op.drop_column('enable_sender_filter')
        batch_op.drop_column('dedup_check_media')
        batch_op.drop_column('dedup_check_content')
        batch_op.drop_column('dedup_time_window')
        batch_op.drop_column('enable_deduplication')

