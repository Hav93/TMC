"""添加文件元数据字段

Revision ID: add_file_metadata_20250111
Revises: add_last_connected_20250108
Create Date: 2025-01-11 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_file_metadata_20250111'
down_revision: Union[str, None] = 'add_pan115_fields_20250110'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加文件元数据字段"""
    # 添加文件唯一ID字段
    op.add_column('download_tasks', sa.Column('file_unique_id', sa.String(length=255), nullable=True, comment='文件唯一ID（用于重新下载）'))
    # 添加文件访问哈希字段
    op.add_column('download_tasks', sa.Column('file_access_hash', sa.String(length=255), nullable=True, comment='文件访问哈希'))
    # 添加媒体信息JSON字段
    op.add_column('download_tasks', sa.Column('media_json', sa.Text(), nullable=True, comment='媒体信息JSON（用于恢复下载）'))


def downgrade() -> None:
    """删除文件元数据字段"""
    op.drop_column('download_tasks', 'media_json')
    op.drop_column('download_tasks', 'file_access_hash')
    op.drop_column('download_tasks', 'file_unique_id')

