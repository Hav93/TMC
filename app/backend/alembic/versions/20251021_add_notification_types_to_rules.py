"""
Add notification_types (JSON list) to notification_rules

Revision ID: 20251021_add_notification_types_to_rules
Revises: 20251020_add_type_specific_paths_to_resource_rules
Create Date: 2025-10-21
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251021_add_notification_types_to_rules'
down_revision = '20251020_add_type_specific_paths_to_resource_rules'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.add_column('notification_rules', sa.Column('notification_types', sa.Text(), nullable=True))
    except Exception:
        pass


def downgrade():
    try:
        op.drop_column('notification_rules', 'notification_types')
    except Exception:
        pass


