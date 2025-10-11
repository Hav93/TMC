"""rename clouddrive_path to pan115_path

Revision ID: rename_clouddrive_to_pan115
Revises: remove_clouddrive_20250111
Create Date: 2025-01-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rename_clouddrive_to_pan115'
down_revision = 'remove_clouddrive_20250111'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """重命名 clouddrive_path 为 pan115_path"""
    # SQLite 不支持直接重命名列，使用batch模式重建表
    with op.batch_alter_table('media_files', schema=None) as batch_op:
        # 添加新列
        batch_op.add_column(sa.Column('pan115_path', sa.String(length=500), nullable=True, comment='115网盘远程路径'))
    
    # 复制数据
    op.execute('UPDATE media_files SET pan115_path = clouddrive_path WHERE clouddrive_path IS NOT NULL')
    
    # 删除旧列
    with op.batch_alter_table('media_files', schema=None) as batch_op:
        batch_op.drop_column('clouddrive_path')


def downgrade() -> None:
    """回滚：pan115_path 改回 clouddrive_path"""
    # 添加旧列
    with op.batch_alter_table('media_files', schema=None) as batch_op:
        batch_op.add_column(sa.Column('clouddrive_path', sa.String(length=500), nullable=True, comment='CloudDrive远程路径'))
    
    # 复制数据回去
    op.execute('UPDATE media_files SET clouddrive_path = pan115_path WHERE pan115_path IS NOT NULL')
    
    # 删除新列
    with op.batch_alter_table('media_files', schema=None) as batch_op:
        batch_op.drop_column('pan115_path')
