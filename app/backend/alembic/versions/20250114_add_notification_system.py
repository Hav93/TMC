"""add notification system

Revision ID: 20250114_add_notification_system
Revises: 20250114_add_resource_monitor
Create Date: 2025-01-14 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250114_add_notification_system'
down_revision = '20250114_add_resource_monitor'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 notification_rules 表
    op.create_table(
        'notification_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID（NULL表示全局规则）'),
        sa.Column('notification_type', sa.String(length=50), nullable=False, comment='通知类型'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否启用'),
        
        # 通知渠道配置
        sa.Column('telegram_chat_id', sa.String(length=50), nullable=True, comment='Telegram聊天ID'),
        sa.Column('telegram_enabled', sa.Boolean(), nullable=True, comment='是否启用Telegram通知'),
        sa.Column('webhook_url', sa.String(length=500), nullable=True, comment='Webhook URL'),
        sa.Column('webhook_enabled', sa.Boolean(), nullable=True, comment='是否启用Webhook'),
        sa.Column('email_address', sa.String(length=200), nullable=True, comment='邮箱地址'),
        sa.Column('email_enabled', sa.Boolean(), nullable=True, comment='是否启用邮件通知'),
        
        # 通知频率控制
        sa.Column('min_interval', sa.Integer(), nullable=True, comment='最小间隔（秒），0表示不限制'),
        sa.Column('max_per_hour', sa.Integer(), nullable=True, comment='每小时最大数量，0表示不限制'),
        sa.Column('last_sent_at', sa.DateTime(), nullable=True, comment='最后发送时间'),
        sa.Column('sent_count_hour', sa.Integer(), nullable=True, comment='当前小时已发送数量'),
        sa.Column('hour_reset_at', sa.DateTime(), nullable=True, comment='小时计数器重置时间'),
        
        # 通知内容配置
        sa.Column('custom_template', sa.Text(), nullable=True, comment='自定义模板'),
        sa.Column('include_details', sa.Boolean(), nullable=True, comment='是否包含详细信息'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_notification_rules_type', 'notification_rules', ['notification_type'])
    op.create_index('idx_notification_rules_user_id', 'notification_rules', ['user_id'])
    
    # 创建 notification_logs 表
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False, comment='通知类型'),
        sa.Column('message', sa.Text(), nullable=False, comment='通知消息'),
        sa.Column('channels', sa.String(length=200), nullable=True, comment='通知渠道（逗号分隔）'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
        
        # 发送状态
        sa.Column('status', sa.String(length=20), nullable=True, comment='发送状态：pending/sent/failed'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        
        # 关联信息
        sa.Column('related_type', sa.String(length=50), nullable=True, comment='关联类型：resource/media/forward'),
        sa.Column('related_id', sa.Integer(), nullable=True, comment='关联ID'),
        
        # 时间戳
        sa.Column('sent_at', sa.DateTime(), nullable=True, comment='发送时间'),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_notification_logs_type', 'notification_logs', ['notification_type'])
    op.create_index('idx_notification_logs_sent_at', 'notification_logs', ['sent_at'])
    op.create_index('idx_notification_logs_user_id', 'notification_logs', ['user_id'])


def downgrade():
    # 删除索引
    op.drop_index('idx_notification_logs_user_id', table_name='notification_logs')
    op.drop_index('idx_notification_logs_sent_at', table_name='notification_logs')
    op.drop_index('idx_notification_logs_type', table_name='notification_logs')
    op.drop_index('idx_notification_rules_user_id', table_name='notification_rules')
    op.drop_index('idx_notification_rules_type', table_name='notification_rules')
    
    # 删除表
    op.drop_table('notification_logs')
    op.drop_table('notification_rules')

