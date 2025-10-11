"""rename clouddrive_path to pan115_path

Revision ID: rename_clouddrive_to_pan115
Revises: 
Create Date: 2025-01-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rename_clouddrive_to_pan115'
down_revision = None  # 设置为您的最新迁移ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    """重命名 clouddrive_path 为 pan115_path"""
    # SQLite 不支持直接重命名列，需要使用 batch 模式
    with op.batch_alter_table('media_files') as batch_op:
        # 检查列是否存在，如果存在则重命名
        try:
            batch_op.alter_column(
                'clouddrive_path',
                new_column_name='pan115_path',
                existing_type=sa.String(500),
                existing_comment='115网盘远程路径'
            )
        except Exception:
            # 如果列不存在或已经是 pan115_path，跳过
            pass


def downgrade() -> None:
    """回滚：pan115_path 改回 clouddrive_path"""
    with op.batch_alter_table('media_files') as batch_op:
        try:
            batch_op.alter_column(
                'pan115_path',
                new_column_name='clouddrive_path',
                existing_type=sa.String(500),
                existing_comment='CloudDrive远程路径'
            )
        except Exception:
            pass

