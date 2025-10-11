"""Remove CloudDrive fields

Revision ID: remove_clouddrive_20250111
Revises: add_file_metadata_20250111
Create Date: 2025-01-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'remove_clouddrive_20250111'
down_revision: Union[str, None] = 'add_file_metadata_20250111'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 删除 media_monitor_rules 表的 CloudDrive 字段
    with op.batch_alter_table('media_monitor_rules') as batch_op:
        batch_op.drop_column('organize_clouddrive_mount')
        batch_op.drop_column('clouddrive_enabled')
        batch_op.drop_column('clouddrive_url')
        batch_op.drop_column('clouddrive_username')
        batch_op.drop_column('clouddrive_password')
        batch_op.drop_column('clouddrive_remote_path')
    
    # 删除 media_settings 表的 CloudDrive 字段
    with op.batch_alter_table('media_settings') as batch_op:
        batch_op.drop_column('clouddrive_enabled')
        batch_op.drop_column('clouddrive_url')
        batch_op.drop_column('clouddrive_username')
        batch_op.drop_column('clouddrive_password')
        batch_op.drop_column('clouddrive_remote_path')


def downgrade() -> None:
    # 恢复 media_settings 表的 CloudDrive 字段
    with op.batch_alter_table('media_settings') as batch_op:
        batch_op.add_column(sa.Column('clouddrive_enabled', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('clouddrive_url', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('clouddrive_username', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('clouddrive_password', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('clouddrive_remote_path', sa.String(length=500), nullable=True))
    
    # 恢复 media_monitor_rules 表的 CloudDrive 字段
    with op.batch_alter_table('media_monitor_rules') as batch_op:
        batch_op.add_column(sa.Column('organize_clouddrive_mount', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('clouddrive_enabled', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('clouddrive_url', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('clouddrive_username', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('clouddrive_password', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('clouddrive_remote_path', sa.String(length=255), nullable=True))

