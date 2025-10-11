"""Initial schema

Revision ID: initial_schema_001
Revises: 
Create Date: 2025-10-05

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'initial_schema_001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级到初始模式"""
    # 创建 forward_rules 表
    op.create_table(
        'forward_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='规则名称'),
        sa.Column('source_chat_id', sa.String(length=50), nullable=False, comment='源聊天ID'),
        sa.Column('source_chat_name', sa.String(length=200), nullable=True, comment='源聊天名称'),
        sa.Column('target_chat_id', sa.String(length=50), nullable=False, comment='目标聊天ID'),
        sa.Column('target_chat_name', sa.String(length=200), nullable=True, comment='目标聊天名称'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('enable_keyword_filter', sa.Boolean(), nullable=True, comment='是否启用关键词过滤'),
        sa.Column('enable_regex_replace', sa.Boolean(), nullable=True, comment='是否启用正则替换'),
        sa.Column('forward_text', sa.Boolean(), nullable=True, comment='转发文本'),
        sa.Column('forward_image', sa.Boolean(), nullable=True, comment='转发图片'),
        sa.Column('forward_video', sa.Boolean(), nullable=True, comment='转发视频'),
        sa.Column('forward_file', sa.Boolean(), nullable=True, comment='转发文件'),
        sa.Column('forward_audio', sa.Boolean(), nullable=True, comment='转发音频'),
        sa.Column('forward_voice', sa.Boolean(), nullable=True, comment='转发语音'),
        sa.Column('forward_sticker', sa.Boolean(), nullable=True, comment='转发贴纸'),
        sa.Column('forward_gif', sa.Boolean(), nullable=True, comment='转发GIF'),
        sa.Column('forward_link', sa.Boolean(), nullable=True, comment='转发链接'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建 keywords 表
    op.create_table(
        'keywords',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False, comment='所属规则ID'),
        sa.Column('keyword', sa.String(length=200), nullable=False, comment='关键词'),
        sa.Column('match_type', sa.String(length=20), nullable=True, comment='匹配类型：contain/exact/regex'),
        sa.Column('is_exclude', sa.Boolean(), nullable=True, comment='是否为排除关键词'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['rule_id'], ['forward_rules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建 replace_rules 表
    op.create_table(
        'replace_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False, comment='所属规则ID'),
        sa.Column('pattern', sa.String(length=500), nullable=False, comment='正则表达式'),
        sa.Column('replacement', sa.Text(), nullable=True, comment='替换内容'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['rule_id'], ['forward_rules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建 message_logs 表
    op.create_table(
        'message_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_name', sa.String(length=100), nullable=True, comment='规则名称'),
        sa.Column('source_chat_id', sa.String(length=50), nullable=True, comment='源聊天ID'),
        sa.Column('source_chat_name', sa.String(length=200), nullable=True, comment='源聊天名称'),
        sa.Column('target_chat_id', sa.String(length=50), nullable=True, comment='目标聊天ID'),
        sa.Column('target_chat_name', sa.String(length=200), nullable=True, comment='目标聊天名称'),
        sa.Column('message_id', sa.String(length=50), nullable=True, comment='消息ID'),
        sa.Column('message_text', sa.Text(), nullable=True, comment='消息文本'),
        sa.Column('message_type', sa.String(length=50), nullable=True, comment='消息类型'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='状态：success/failed'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建 telegram_clients 表
    op.create_table(
        'telegram_clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(length=100), nullable=False, comment='客户端标识'),
        sa.Column('client_type', sa.String(length=20), nullable=False, comment='客户端类型：user/bot'),
        sa.Column('phone', sa.String(length=50), nullable=True, comment='手机号'),
        sa.Column('api_id', sa.String(length=50), nullable=True, comment='API ID'),
        sa.Column('api_hash', sa.String(length=100), nullable=True, comment='API Hash'),
        sa.Column('bot_token', sa.String(length=200), nullable=True, comment='Bot Token'),
        sa.Column('session_file', sa.String(length=200), nullable=True, comment='会话文件路径'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('auto_start', sa.Boolean(), nullable=True, comment='自动启动'),
        sa.Column('last_used', sa.DateTime(), nullable=True, comment='最后使用时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id')
    )


def downgrade() -> None:
    """降级：删除所有表"""
    op.drop_table('telegram_clients')
    op.drop_table('message_logs')
    op.drop_table('replace_rules')
    op.drop_table('keywords')
    op.drop_table('forward_rules')

