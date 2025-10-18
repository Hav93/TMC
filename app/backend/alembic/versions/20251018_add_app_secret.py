"""add pan115_app_secret

Revision ID: 20251018_add_app_secret
Revises: 20251018_fix_missing_columns
Create Date: 2025-10-18 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251018_add_app_secret'
down_revision = '20251018_fix_missing_columns'
branch_labels = None
depends_on = None


def upgrade():
    # 检查列是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('media_settings')]
    
    # 添加pan115_app_secret字段（如果不存在）
    if 'pan115_app_secret' not in columns:
        op.add_column('media_settings', sa.Column('pan115_app_secret', sa.String(length=100), nullable=True, comment='115开放平台AppSecret'))
        print(" ✅ 添加 media_settings.pan115_app_secret")
    else:
        print(" ⏭️  media_settings.pan115_app_secret 已存在，跳过")


def downgrade():
    op.drop_column('media_settings', 'pan115_app_secret')

