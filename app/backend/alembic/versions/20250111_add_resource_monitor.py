"""add resource monitor tables

Revision ID: 20250111_add_resource_monitor
Revises: test_branch_init
Create Date: 2025-01-11 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250111_add_resource_monitor'
down_revision = 'test_branch_init'
branch_labels = None
depends_on = None


def upgrade():
    # 创建资源监控规则表
    op.create_table(
        'resource_monitor_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='规则名称'),
        sa.Column('source_chats', sa.Text(), nullable=True, comment='监控的群组/频道ID列表(JSON)'),
        sa.Column('include_keywords', sa.Text(), nullable=True, comment='包含关键词(JSON)'),
        sa.Column('exclude_keywords', sa.Text(), nullable=True, comment='排除关键词(JSON)'),
        sa.Column('monitor_pan115', sa.Boolean(), nullable=True, comment='是否监控115分享链接'),
        sa.Column('monitor_magnet', sa.Boolean(), nullable=True, comment='是否监控磁力链接'),
        sa.Column('monitor_ed2k', sa.Boolean(), nullable=True, comment='是否监控ed2k链接'),
        sa.Column('target_path', sa.String(length=500), nullable=True, comment='115网盘目标路径'),
        sa.Column('auto_save', sa.Boolean(), nullable=True, comment='是否自动转存到115'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('total_captured', sa.Integer(), nullable=True, comment='总捕获数'),
        sa.Column('total_saved', sa.Integer(), nullable=True, comment='总转存数'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建资源记录表
    op.create_table(
        'resource_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False, comment='规则ID'),
        sa.Column('message_text', sa.Text(), nullable=True, comment='完整消息文本'),
        sa.Column('message_snapshot', sa.Text(), nullable=True, comment='消息快照(JSON)'),
        sa.Column('chat_id', sa.String(length=50), nullable=True, comment='群组/频道ID'),
        sa.Column('chat_title', sa.String(length=200), nullable=True, comment='群组/频道名称'),
        sa.Column('message_id', sa.Integer(), nullable=True, comment='消息ID'),
        sa.Column('sender_id', sa.String(length=50), nullable=True, comment='发送者ID'),
        sa.Column('sender_name', sa.String(length=200), nullable=True, comment='发送者名称'),
        sa.Column('pan115_links', sa.Text(), nullable=True, comment='115分享链接(JSON)'),
        sa.Column('magnet_links', sa.Text(), nullable=True, comment='磁力链接(JSON)'),
        sa.Column('ed2k_links', sa.Text(), nullable=True, comment='ed2k链接(JSON)'),
        sa.Column('link_fingerprint', sa.String(length=64), nullable=True, comment='链接指纹(MD5)'),
        sa.Column('tags', sa.Text(), nullable=True, comment='标签(JSON)'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='状态: pending/saved/failed/ignored'),
        sa.Column('target_path', sa.String(length=500), nullable=True, comment='实际保存路径'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('pan115_task_id', sa.String(length=100), nullable=True, comment='115任务ID'),
        sa.Column('saved_at', sa.DateTime(), nullable=True, comment='转存时间'),
        sa.Column('detected_at', sa.DateTime(), nullable=True, comment='捕获时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['rule_id'], ['resource_monitor_rules.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('link_fingerprint')
    )
    
    # 创建索引
    op.create_index('idx_resource_records_rule_id', 'resource_records', ['rule_id'])
    op.create_index('idx_resource_records_status', 'resource_records', ['status'])
    op.create_index('idx_resource_records_chat_id', 'resource_records', ['chat_id'])
    op.create_index('idx_resource_records_detected_at', 'resource_records', ['detected_at'])


def downgrade():
    op.drop_index('idx_resource_records_detected_at', table_name='resource_records')
    op.drop_index('idx_resource_records_chat_id', table_name='resource_records')
    op.drop_index('idx_resource_records_status', table_name='resource_records')
    op.drop_index('idx_resource_records_rule_id', table_name='resource_records')
    op.drop_table('resource_records')
    op.drop_table('resource_monitor_rules')

