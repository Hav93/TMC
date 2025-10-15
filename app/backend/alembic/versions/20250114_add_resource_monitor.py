"""add resource monitor tables

Revision ID: 20250114_add_resource_monitor
Revises: 20250114_initial_schema
Create Date: 2025-01-14 10:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250114_add_resource_monitor'
down_revision = '20250114_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """创建资源监控相关表"""
    
    # 1. 创建 resource_monitor_rules 表
    op.create_table(
        'resource_monitor_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='规则名称'),
        sa.Column('source_chats', sa.Text(), nullable=False, comment='源聊天列表(JSON)'),
        sa.Column('is_active', sa.Boolean(), default=True, comment='是否启用'),
        sa.Column('link_types', sa.Text(), comment='链接类型(JSON): ["pan115", "magnet", "ed2k"]'),
        sa.Column('keywords', sa.Text(), comment='关键词(JSON)'),
        sa.Column('auto_save_to_115', sa.Boolean(), default=False, comment='是否自动转存到115'),
        sa.Column('target_path', sa.String(length=500), comment='目标路径'),
        sa.Column('pan115_user_key', sa.String(length=100), comment='115用户密钥（可选）'),
        sa.Column('default_tags', sa.Text(), comment='默认标签(JSON)'),
        sa.Column('enable_deduplication', sa.Boolean(), default=True, comment='是否启用去重'),
        sa.Column('dedup_time_window', sa.Integer(), default=3600, comment='去重时间窗口(秒)'),
        sa.Column('created_at', sa.DateTime(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 2. 创建 resource_records 表
    op.create_table(
        'resource_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('rule_name', sa.String(length=100), comment='规则名称（冗余）'),
        sa.Column('source_chat_id', sa.String(length=50), comment='源聊天ID'),
        sa.Column('source_chat_name', sa.String(length=200), comment='源聊天名称'),
        sa.Column('message_id', sa.Integer(), comment='消息ID'),
        sa.Column('message_text', sa.Text(), comment='消息文本'),
        sa.Column('message_date', sa.DateTime(), comment='消息时间'),
        sa.Column('link_type', sa.String(length=20), comment='链接类型'),
        sa.Column('link_url', sa.Text(), nullable=False, comment='链接URL'),
        sa.Column('link_hash', sa.String(length=64), comment='链接哈希（用于去重）'),
        sa.Column('save_status', sa.String(length=20), default='pending', comment='转存状态'),
        sa.Column('save_path', sa.String(length=500), comment='转存路径'),
        sa.Column('save_error', sa.Text(), comment='转存错误信息'),
        sa.Column('save_time', sa.DateTime(), comment='转存时间'),
        sa.Column('retry_count', sa.Integer(), default=0, comment='重试次数'),
        sa.Column('tags', sa.Text(), comment='标签(JSON)'),
        sa.Column('message_snapshot', sa.Text(), comment='消息快照(JSON)'),
        sa.Column('created_at', sa.DateTime(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['rule_id'], ['resource_monitor_rules.id'], ondelete='CASCADE')
    )
    
    # 3. 创建索引
    op.create_index('idx_resource_records_link_hash', 'resource_records', ['link_hash'])
    op.create_index('idx_resource_records_save_status', 'resource_records', ['save_status'])
    op.create_index('idx_resource_records_created_at', 'resource_records', ['created_at'])


def downgrade():
    """删除资源监控相关表"""
    op.drop_index('idx_resource_records_created_at', table_name='resource_records')
    op.drop_index('idx_resource_records_save_status', table_name='resource_records')
    op.drop_index('idx_resource_records_link_hash', table_name='resource_records')
    op.drop_table('resource_records')
    op.drop_table('resource_monitor_rules')

