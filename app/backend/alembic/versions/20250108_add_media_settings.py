"""Add media_settings table for global configuration

Revision ID: 20250108_add_media_settings
Revises: 20250108_add_last_connected
Create Date: 2025-10-08 19:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250108_add_media_settings'
down_revision = '20250108_add_last_connected'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建媒体管理全局配置表"""
    op.create_table('media_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        
        # CloudDrive 配置
        sa.Column('clouddrive_enabled', sa.Boolean(), nullable=True, comment='启用CloudDrive'),
        sa.Column('clouddrive_url', sa.String(length=200), nullable=True, comment='CloudDrive服务地址'),
        sa.Column('clouddrive_username', sa.String(length=100), nullable=True, comment='CloudDrive用户名'),
        sa.Column('clouddrive_password', sa.String(length=200), nullable=True, comment='CloudDrive密码(加密存储)'),
        sa.Column('clouddrive_remote_path', sa.String(length=500), nullable=True, comment='CloudDrive远程路径'),
        
        # 下载设置
        sa.Column('temp_folder', sa.String(length=500), nullable=True, comment='临时下载文件夹'),
        sa.Column('concurrent_downloads', sa.Integer(), nullable=True, comment='并发下载数'),
        sa.Column('retry_on_failure', sa.Boolean(), nullable=True, comment='失败时重试'),
        sa.Column('max_retries', sa.Integer(), nullable=True, comment='最大重试次数'),
        
        # 元数据提取
        sa.Column('extract_metadata', sa.Boolean(), nullable=True, comment='提取元数据'),
        sa.Column('metadata_mode', sa.String(length=20), nullable=True, comment='提取模式：disabled/lightweight/full'),
        sa.Column('metadata_timeout', sa.Integer(), nullable=True, comment='超时时间(秒)'),
        sa.Column('async_metadata_extraction', sa.Boolean(), nullable=True, comment='异步提取元数据'),
        
        # 存储清理
        sa.Column('auto_cleanup_enabled', sa.Boolean(), nullable=True, comment='启用自动清理'),
        sa.Column('auto_cleanup_days', sa.Integer(), nullable=True, comment='临时文件保留天数'),
        sa.Column('cleanup_only_organized', sa.Boolean(), nullable=True, comment='只清理已归档文件'),
        sa.Column('max_storage_gb', sa.Integer(), nullable=True, comment='最大存储容量(GB)'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # 插入默认配置
    op.execute("""
        INSERT INTO media_settings (
            clouddrive_enabled, clouddrive_remote_path,
            temp_folder, concurrent_downloads, retry_on_failure, max_retries,
            extract_metadata, metadata_mode, metadata_timeout, async_metadata_extraction,
            auto_cleanup_enabled, auto_cleanup_days, cleanup_only_organized, max_storage_gb,
            created_at, updated_at
        ) VALUES (
            0, '/Media',
            '/app/media/downloads', 3, 1, 3,
            1, 'lightweight', 10, 1,
            1, 7, 1, 100,
            datetime('now'), datetime('now')
        )
    """)


def downgrade() -> None:
    """删除媒体管理全局配置表"""
    op.drop_table('media_settings')

