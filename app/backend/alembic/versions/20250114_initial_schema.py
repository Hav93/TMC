"""initial schema - create all core tables

Revision ID: 20250114_initial_schema
Revises: 
Create Date: 2025-01-14 09:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250114_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建所有核心表"""
    
    # 1. 创建 users 表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False, unique=True),
        sa.Column('email', sa.String(length=100)),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100)),
        sa.Column('avatar', sa.String(length=500)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('last_login', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 2. 创建 telegram_clients 表
    op.create_table(
        'telegram_clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(length=100), nullable=False, unique=True),
        sa.Column('client_type', sa.String(length=20), default='user'),
        sa.Column('bot_token', sa.String(length=200)),
        sa.Column('admin_user_id', sa.Integer()),
        sa.Column('api_id', sa.Integer()),
        sa.Column('api_hash', sa.String(length=100)),
        sa.Column('phone', sa.String(length=20)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('auto_start', sa.Boolean(), default=False),
        sa.Column('last_connected', sa.DateTime()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 3. 创建 bot_settings 表
    op.create_table(
        'bot_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False, unique=True),
        sa.Column('value', sa.Text()),
        sa.Column('description', sa.Text()),
        sa.Column('is_secret', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 4. 创建 user_sessions 表
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False, unique=True),
        sa.Column('ip_address', sa.String(length=50)),
        sa.Column('user_agent', sa.String(length=500)),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('last_active', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # 5. 创建 forward_rules 表
    op.create_table(
        'forward_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('source_chat_id', sa.String(length=50), nullable=False),
        sa.Column('source_chat_name', sa.String(length=200)),
        sa.Column('target_chat_id', sa.String(length=50), nullable=False),
        sa.Column('target_chat_name', sa.String(length=200)),
        
        # 功能开关
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('enable_keyword_filter', sa.Boolean(), default=False),
        sa.Column('enable_regex_replace', sa.Boolean(), default=False),
        
        # 客户端选择
        sa.Column('client_id', sa.String(length=50), default='main_user'),
        sa.Column('client_type', sa.String(length=20), default='user'),
        
        # 消息类型支持
        sa.Column('enable_text', sa.Boolean(), default=True),
        sa.Column('enable_media', sa.Boolean(), default=True),
        sa.Column('enable_photo', sa.Boolean(), default=True),
        sa.Column('enable_video', sa.Boolean(), default=True),
        sa.Column('enable_document', sa.Boolean(), default=True),
        sa.Column('enable_audio', sa.Boolean(), default=True),
        sa.Column('enable_voice', sa.Boolean(), default=True),
        sa.Column('enable_sticker', sa.Boolean(), default=False),
        sa.Column('enable_animation', sa.Boolean(), default=True),
        sa.Column('enable_webpage', sa.Boolean(), default=True),
        
        # 高级设置
        sa.Column('forward_delay', sa.Integer(), default=0),
        sa.Column('max_message_length', sa.Integer(), default=4096),
        sa.Column('enable_link_preview', sa.Boolean(), default=True),
        
        # 时间过滤设置
        sa.Column('time_filter_type', sa.String(length=20), default='after_start'),
        sa.Column('start_time', sa.DateTime()),
        sa.Column('end_time', sa.DateTime()),
        
        # 消息去重设置
        sa.Column('enable_deduplication', sa.Boolean(), default=False),
        sa.Column('dedup_time_window', sa.Integer(), default=3600),
        sa.Column('dedup_check_content', sa.Boolean(), default=True),
        sa.Column('dedup_check_media', sa.Boolean(), default=True),
        
        # 发送者过滤设置
        sa.Column('enable_sender_filter', sa.Boolean(), default=False),
        sa.Column('sender_filter_mode', sa.String(length=20), default='whitelist'),
        sa.Column('sender_whitelist', sa.Text()),
        sa.Column('sender_blacklist', sa.Text()),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 6. 创建 keywords 表
    op.create_table(
        'keywords',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('keyword', sa.String(length=500), nullable=False),
        sa.Column('match_type', sa.String(length=20), default='contains'),
        sa.Column('is_regex', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['rule_id'], ['forward_rules.id'], ondelete='CASCADE')
    )
    
    # 7. 创建 replace_rules 表
    op.create_table(
        'replace_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('pattern', sa.String(length=500), nullable=False),
        sa.Column('replacement', sa.String(length=500)),
        sa.Column('is_regex', sa.Boolean(), default=False),
        sa.Column('priority', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['rule_id'], ['forward_rules.id'], ondelete='CASCADE')
    )
    
    # 8. 创建 message_logs 表
    op.create_table(
        'message_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer()),
        sa.Column('rule_name', sa.String(length=100)),
        sa.Column('source_chat_id', sa.String(length=50)),
        sa.Column('source_chat_name', sa.String(length=200)),
        sa.Column('target_chat_id', sa.String(length=50)),
        sa.Column('target_chat_name', sa.String(length=200)),
        sa.Column('original_message_id', sa.Integer()),
        sa.Column('forwarded_message_id', sa.Integer()),
        sa.Column('message_type', sa.String(length=50)),
        sa.Column('message_text', sa.Text()),
        sa.Column('message_size_mb', sa.Float()),
        sa.Column('status', sa.String(length=20), default='success'),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 9. 创建 media_monitor_rules 表
    op.create_table(
        'media_monitor_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('client_id', sa.String(length=100)),
        sa.Column('source_chats', sa.Text(), nullable=False),
        sa.Column('media_types', sa.Text()),
        sa.Column('min_size_mb', sa.Float()),
        sa.Column('max_size_mb', sa.Float()),
        sa.Column('filename_include', sa.Text()),
        sa.Column('filename_exclude', sa.Text()),
        sa.Column('file_extensions', sa.Text()),
        sa.Column('enable_sender_filter', sa.Boolean(), default=False),
        sa.Column('sender_filter_mode', sa.String(length=20), default='whitelist'),
        sa.Column('sender_whitelist', sa.Text()),
        sa.Column('sender_blacklist', sa.Text()),
        sa.Column('temp_folder', sa.String(length=500)),
        sa.Column('concurrent_downloads', sa.Integer(), default=3),
        sa.Column('retry_on_failure', sa.Boolean(), default=True),
        sa.Column('max_retries', sa.Integer(), default=3),
        sa.Column('extract_metadata', sa.Boolean(), default=True),
        sa.Column('metadata_mode', sa.String(length=20), default='auto'),
        sa.Column('metadata_timeout', sa.Integer(), default=30),
        sa.Column('async_metadata_extraction', sa.Boolean(), default=False),
        sa.Column('organize_enabled', sa.Boolean(), default=False),
        sa.Column('organize_target_type', sa.String(length=20)),
        sa.Column('organize_local_path', sa.String(length=500)),
        sa.Column('organize_mode', sa.String(length=20), default='copy'),
        sa.Column('keep_temp_file', sa.Boolean(), default=False),
        sa.Column('pan115_remote_path', sa.String(length=500)),
        sa.Column('folder_structure', sa.String(length=50), default='flat'),
        sa.Column('custom_folder_template', sa.String(length=500)),
        sa.Column('rename_files', sa.Boolean(), default=False),
        sa.Column('filename_template', sa.String(length=500)),
        sa.Column('auto_cleanup_enabled', sa.Boolean(), default=False),
        sa.Column('auto_cleanup_days', sa.Integer(), default=7),
        sa.Column('cleanup_only_organized', sa.Boolean(), default=True),
        sa.Column('max_storage_gb', sa.Float()),
        sa.Column('total_downloaded', sa.Integer(), default=0),
        sa.Column('total_size_mb', sa.Float(), default=0.0),
        sa.Column('last_download_at', sa.DateTime()),
        sa.Column('failed_downloads', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 10. 创建 download_tasks 表
    op.create_table(
        'download_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('monitor_rule_id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer()),
        sa.Column('chat_id', sa.String(length=50)),
        sa.Column('file_name', sa.String(length=500)),
        sa.Column('file_type', sa.String(length=50)),
        sa.Column('file_size_mb', sa.Float()),
        sa.Column('file_unique_id', sa.String(length=100)),
        sa.Column('file_access_hash', sa.String(length=100)),
        sa.Column('media_json', sa.Text()),
        sa.Column('status', sa.String(length=20), default='pending'),
        sa.Column('priority', sa.Integer(), default=5),
        sa.Column('downloaded_bytes', sa.BigInteger(), default=0),
        sa.Column('total_bytes', sa.BigInteger()),
        sa.Column('progress_percent', sa.Float(), default=0.0),
        sa.Column('download_speed_mbps', sa.Float()),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('max_retries', sa.Integer(), default=3),
        sa.Column('last_error', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('failed_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['monitor_rule_id'], ['media_monitor_rules.id'], ondelete='CASCADE')
    )
    
    # 11. 创建 media_settings 表
    op.create_table(
        'media_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pan115_app_id', sa.String(length=100)),
        sa.Column('pan115_user_id', sa.String(length=100)),
        sa.Column('pan115_user_key', sa.String(length=200)),
        sa.Column('pan115_request_interval', sa.Integer(), default=1000),
        sa.Column('pan115_device_type', sa.String(length=50), default='web'),
        sa.Column('temp_folder', sa.String(length=500), default='media/downloads'),
        sa.Column('concurrent_downloads', sa.Integer(), default=3),
        sa.Column('retry_on_failure', sa.Boolean(), default=True),
        sa.Column('max_retries', sa.Integer(), default=3),
        sa.Column('extract_metadata', sa.Boolean(), default=True),
        sa.Column('metadata_mode', sa.String(length=20), default='auto'),
        sa.Column('metadata_timeout', sa.Integer(), default=30),
        sa.Column('async_metadata_extraction', sa.Boolean(), default=False),
        sa.Column('auto_cleanup_enabled', sa.Boolean(), default=False),
        sa.Column('auto_cleanup_days', sa.Integer(), default=7),
        sa.Column('cleanup_only_organized', sa.Boolean(), default=True),
        sa.Column('max_storage_gb', sa.Float()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 12. 创建 media_files 表
    op.create_table(
        'media_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('monitor_rule_id', sa.Integer(), nullable=False),
        sa.Column('download_task_id', sa.Integer()),
        sa.Column('message_id', sa.Integer()),
        
        # 文件路径
        sa.Column('temp_path', sa.String(length=500)),
        sa.Column('final_path', sa.String(length=500)),
        sa.Column('pan115_path', sa.String(length=500)),
        sa.Column('file_hash', sa.String(length=64), unique=True),
        
        # 基础信息
        sa.Column('file_name', sa.String(length=255)),
        sa.Column('file_type', sa.String(length=50)),
        sa.Column('file_size_mb', sa.Integer()),
        sa.Column('extension', sa.String(length=10)),
        sa.Column('original_name', sa.String(length=255)),
        
        # 元数据
        sa.Column('file_metadata', sa.Text()),
        
        # 快捷字段
        sa.Column('width', sa.Integer()),
        sa.Column('height', sa.Integer()),
        sa.Column('duration_seconds', sa.Integer()),
        sa.Column('resolution', sa.String(length=20)),
        sa.Column('codec', sa.String(length=50)),
        sa.Column('bitrate_kbps', sa.Integer()),
        
        # 来源信息
        sa.Column('source_chat', sa.String(length=100)),
        sa.Column('sender_id', sa.String(length=50)),
        sa.Column('sender_username', sa.String(length=100)),
        
        # 状态
        sa.Column('is_organized', sa.Boolean(), default=False),
        sa.Column('is_uploaded_to_cloud', sa.Boolean(), default=False),
        sa.Column('is_starred', sa.Boolean(), default=False),
        sa.Column('organize_failed', sa.Boolean(), default=False),
        sa.Column('organize_error', sa.Text()),
        
        # 时间戳
        sa.Column('downloaded_at', sa.DateTime()),
        sa.Column('organized_at', sa.DateTime()),
        sa.Column('uploaded_at', sa.DateTime()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['download_task_id'], ['download_tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['monitor_rule_id'], ['media_monitor_rules.id'], ondelete='CASCADE')
    )
    
    # 创建索引
    op.create_index('idx_message_logs_created_at', 'message_logs', ['created_at'])
    op.create_index('idx_download_tasks_status', 'download_tasks', ['status'])
    op.create_index('idx_media_files_downloaded_at', 'media_files', ['downloaded_at'])


def downgrade():
    """删除所有核心表"""
    op.drop_index('idx_media_files_downloaded_at', table_name='media_files')
    op.drop_index('idx_download_tasks_status', table_name='download_tasks')
    op.drop_index('idx_message_logs_created_at', table_name='message_logs')
    
    op.drop_table('media_files')
    op.drop_table('media_settings')
    op.drop_table('download_tasks')
    op.drop_table('media_monitor_rules')
    op.drop_table('message_logs')
    op.drop_table('replace_rules')
    op.drop_table('keywords')
    op.drop_table('forward_rules')
    op.drop_table('user_sessions')
    op.drop_table('bot_settings')
    op.drop_table('telegram_clients')
    op.drop_table('users')

