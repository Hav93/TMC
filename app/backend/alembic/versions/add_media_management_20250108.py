"""add media management tables

Revision ID: add_media_management_20250108
Revises: add_dedup_and_sender_filter_20251008
Create Date: 2025-01-08 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_media_management_20250108'
down_revision = 'add_dedup_and_sender_filter_20251008'
branch_labels = None
depends_on = None


def upgrade():
    """添加媒体文件管理相关表"""
    
    # 创建媒体监控规则表
    op.create_table('media_monitor_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='规则名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='规则描述'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('client_id', sa.String(length=50), nullable=False, comment='使用的客户端ID'),
        
        # 监听源
        sa.Column('source_chats', sa.Text(), nullable=True, comment='监听的频道/群组列表，JSON格式'),
        
        # 媒体过滤
        sa.Column('media_types', sa.Text(), nullable=True, comment='文件类型过滤，JSON格式'),
        sa.Column('min_size_mb', sa.Integer(), nullable=True, comment='最小文件大小(MB)'),
        sa.Column('max_size_mb', sa.Integer(), nullable=True, comment='最大文件大小(MB)'),
        sa.Column('filename_include', sa.Text(), nullable=True, comment='文件名包含关键词'),
        sa.Column('filename_exclude', sa.Text(), nullable=True, comment='文件名排除关键词'),
        sa.Column('file_extensions', sa.Text(), nullable=True, comment='允许的文件扩展名，JSON格式'),
        
        # 发送者过滤
        sa.Column('enable_sender_filter', sa.Boolean(), nullable=True, comment='是否启用发送者过滤'),
        sa.Column('sender_filter_mode', sa.String(length=20), nullable=True, comment='过滤模式：whitelist/blacklist'),
        sa.Column('sender_whitelist', sa.Text(), nullable=True, comment='发送者白名单'),
        sa.Column('sender_blacklist', sa.Text(), nullable=True, comment='发送者黑名单'),
        
        # 下载设置
        sa.Column('temp_folder', sa.String(length=255), nullable=True, comment='临时下载文件夹'),
        sa.Column('concurrent_downloads', sa.Integer(), nullable=True, comment='并发下载数量'),
        sa.Column('retry_on_failure', sa.Boolean(), nullable=True, comment='失败时是否重试'),
        sa.Column('max_retries', sa.Integer(), nullable=True, comment='最大重试次数'),
        
        # 元数据提取
        sa.Column('extract_metadata', sa.Boolean(), nullable=True, comment='是否提取元数据'),
        sa.Column('metadata_mode', sa.String(length=20), nullable=True, comment='元数据提取模式'),
        sa.Column('metadata_timeout', sa.Integer(), nullable=True, comment='元数据提取超时（秒）'),
        sa.Column('async_metadata_extraction', sa.Boolean(), nullable=True, comment='是否异步提取元数据'),
        
        # 归档配置
        sa.Column('organize_enabled', sa.Boolean(), nullable=True, comment='是否启用文件归档'),
        sa.Column('organize_target_type', sa.String(length=20), nullable=True, comment='归档目标'),
        sa.Column('organize_local_path', sa.String(length=255), nullable=True, comment='本地归档路径'),
        sa.Column('organize_clouddrive_mount', sa.String(length=255), nullable=True, comment='CloudDrive挂载路径'),
        sa.Column('organize_mode', sa.String(length=20), nullable=True, comment='归档方式'),
        sa.Column('keep_temp_file', sa.Boolean(), nullable=True, comment='归档后是否保留临时文件'),
        
        # CloudDrive API配置
        sa.Column('clouddrive_enabled', sa.Boolean(), nullable=True, comment='是否启用CloudDrive API上传'),
        sa.Column('clouddrive_url', sa.String(length=255), nullable=True, comment='CloudDrive服务地址'),
        sa.Column('clouddrive_username', sa.String(length=100), nullable=True, comment='CloudDrive用户名'),
        sa.Column('clouddrive_password', sa.String(length=255), nullable=True, comment='CloudDrive密码'),
        sa.Column('clouddrive_remote_path', sa.String(length=255), nullable=True, comment='CloudDrive远程路径'),
        
        # 文件夹结构
        sa.Column('folder_structure', sa.String(length=50), nullable=True, comment='文件夹组织方式'),
        sa.Column('custom_folder_template', sa.String(length=255), nullable=True, comment='自定义文件夹模板'),
        sa.Column('rename_files', sa.Boolean(), nullable=True, comment='是否重命名文件'),
        sa.Column('filename_template', sa.String(length=255), nullable=True, comment='文件名模板'),
        
        # 清理设置
        sa.Column('auto_cleanup_enabled', sa.Boolean(), nullable=True, comment='是否启用自动清理'),
        sa.Column('auto_cleanup_days', sa.Integer(), nullable=True, comment='自动清理天数'),
        sa.Column('cleanup_only_organized', sa.Boolean(), nullable=True, comment='是否只清理已归档文件'),
        
        # 存储容量限制
        sa.Column('max_storage_gb', sa.Integer(), nullable=True, comment='最大存储容量(GB)'),
        
        # 统计数据
        sa.Column('total_downloaded', sa.Integer(), nullable=True, comment='累计下载数量'),
        sa.Column('total_size_mb', sa.Integer(), nullable=True, comment='累计下载大小(MB)'),
        sa.Column('last_download_at', sa.DateTime(), nullable=True, comment='最后下载时间'),
        sa.Column('failed_downloads', sa.Integer(), nullable=True, comment='失败下载数量'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建下载任务表
    op.create_table('download_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('monitor_rule_id', sa.Integer(), nullable=False, comment='关联的监控规则ID'),
        sa.Column('message_id', sa.Integer(), nullable=True, comment='消息ID'),
        sa.Column('chat_id', sa.String(length=50), nullable=True, comment='聊天ID'),
        
        # 文件信息
        sa.Column('file_name', sa.String(length=255), nullable=True, comment='文件名'),
        sa.Column('file_type', sa.String(length=50), nullable=True, comment='文件类型'),
        sa.Column('file_size_mb', sa.Integer(), nullable=True, comment='文件大小(MB)'),
        
        # 任务状态
        sa.Column('status', sa.String(length=20), nullable=True, comment='任务状态'),
        sa.Column('priority', sa.Integer(), nullable=True, comment='优先级'),
        
        # 下载进度
        sa.Column('downloaded_bytes', sa.Integer(), nullable=True, comment='已下载字节数'),
        sa.Column('total_bytes', sa.Integer(), nullable=True, comment='总字节数'),
        sa.Column('progress_percent', sa.Integer(), nullable=True, comment='进度百分比'),
        sa.Column('download_speed_mbps', sa.Integer(), nullable=True, comment='下载速度(MB/s)'),
        
        # 重试信息
        sa.Column('retry_count', sa.Integer(), nullable=True, comment='重试次数'),
        sa.Column('max_retries', sa.Integer(), nullable=True, comment='最大重试次数'),
        sa.Column('last_error', sa.Text(), nullable=True, comment='最后一次错误信息'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='开始下载时间'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        sa.Column('failed_at', sa.DateTime(), nullable=True, comment='失败时间'),
        
        sa.ForeignKeyConstraint(['monitor_rule_id'], ['media_monitor_rules.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_download_tasks_status', 'download_tasks', ['status'])
    op.create_index('idx_download_tasks_priority', 'download_tasks', ['priority', 'created_at'])
    
    # 创建媒体文件表
    op.create_table('media_files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('monitor_rule_id', sa.Integer(), nullable=False, comment='关联的监控规则ID'),
        sa.Column('download_task_id', sa.Integer(), nullable=True, comment='关联的下载任务ID'),
        sa.Column('message_id', sa.Integer(), nullable=True, comment='消息ID'),
        
        # 文件路径
        sa.Column('temp_path', sa.String(length=500), nullable=True, comment='临时文件路径'),
        sa.Column('final_path', sa.String(length=500), nullable=True, comment='最终归档路径'),
        sa.Column('clouddrive_path', sa.String(length=500), nullable=True, comment='CloudDrive远程路径'),
        sa.Column('file_hash', sa.String(length=64), nullable=True, comment='文件哈希(SHA-256)'),
        
        # 基础信息
        sa.Column('file_name', sa.String(length=255), nullable=True, comment='文件名'),
        sa.Column('file_type', sa.String(length=50), nullable=True, comment='文件类型'),
        sa.Column('file_size_mb', sa.Integer(), nullable=True, comment='文件大小(MB)'),
        sa.Column('extension', sa.String(length=10), nullable=True, comment='文件扩展名'),
        sa.Column('original_name', sa.String(length=255), nullable=True, comment='原始文件名'),
        
        # 元数据
        sa.Column('file_metadata', sa.Text(), nullable=True, comment='完整元数据JSON'),
        
        # 快捷字段
        sa.Column('width', sa.Integer(), nullable=True, comment='宽度'),
        sa.Column('height', sa.Integer(), nullable=True, comment='高度'),
        sa.Column('duration_seconds', sa.Integer(), nullable=True, comment='时长'),
        sa.Column('resolution', sa.String(length=20), nullable=True, comment='分辨率'),
        sa.Column('codec', sa.String(length=50), nullable=True, comment='编码格式'),
        sa.Column('bitrate_kbps', sa.Integer(), nullable=True, comment='比特率(kbps)'),
        
        # 来源信息
        sa.Column('source_chat', sa.String(length=100), nullable=True, comment='来源频道/群组'),
        sa.Column('sender_id', sa.String(length=50), nullable=True, comment='发送者ID'),
        sa.Column('sender_username', sa.String(length=100), nullable=True, comment='发送者用户名'),
        
        # 状态
        sa.Column('is_organized', sa.Boolean(), nullable=True, comment='是否已归档'),
        sa.Column('is_uploaded_to_cloud', sa.Boolean(), nullable=True, comment='是否已上传到云端'),
        sa.Column('is_starred', sa.Boolean(), nullable=True, comment='是否收藏'),
        
        # 时间戳
        sa.Column('downloaded_at', sa.DateTime(), nullable=True, comment='下载时间'),
        sa.Column('organized_at', sa.DateTime(), nullable=True, comment='归档时间'),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True, comment='上传时间'),
        
        sa.ForeignKeyConstraint(['download_task_id'], ['download_tasks.id'], ),
        sa.ForeignKeyConstraint(['monitor_rule_id'], ['media_monitor_rules.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_hash')
    )
    
    # 创建索引
    op.create_index('idx_media_files_hash', 'media_files', ['file_hash'])
    op.create_index('idx_media_files_type', 'media_files', ['file_type'])
    op.create_index('idx_media_files_organized', 'media_files', ['is_organized'])
    op.create_index('idx_media_files_starred', 'media_files', ['is_starred'])
    op.create_index('idx_media_files_downloaded_at', 'media_files', ['downloaded_at'])


def downgrade():
    """回滚迁移"""
    
    # 删除索引
    op.drop_index('idx_media_files_downloaded_at', 'media_files')
    op.drop_index('idx_media_files_starred', 'media_files')
    op.drop_index('idx_media_files_organized', 'media_files')
    op.drop_index('idx_media_files_type', 'media_files')
    op.drop_index('idx_media_files_hash', 'media_files')
    
    op.drop_index('idx_download_tasks_priority', 'download_tasks')
    op.drop_index('idx_download_tasks_status', 'download_tasks')
    
    # 删除表
    op.drop_table('media_files')
    op.drop_table('download_tasks')
    op.drop_table('media_monitor_rules')

