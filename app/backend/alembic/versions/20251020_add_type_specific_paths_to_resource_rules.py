"""
Add type-specific target paths to resource monitor rules

Revision ID: 20251020_add_type_specific_paths_to_resource_rules
Revises: 20250114_add_notification_system
Create Date: 2025-10-20
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251020_add_type_specific_paths_to_resource_rules'
down_revision = '20251018_add_app_secret'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.add_column('resource_monitor_rules', sa.Column('target_path_pan115', sa.String(length=500), nullable=True))
    except Exception:
        pass
    try:
        op.add_column('resource_monitor_rules', sa.Column('target_path_magnet', sa.String(length=500), nullable=True))
    except Exception:
        pass
    try:
        op.add_column('resource_monitor_rules', sa.Column('target_path_ed2k', sa.String(length=500), nullable=True))
    except Exception:
        pass


def downgrade():
    try:
        op.drop_column('resource_monitor_rules', 'target_path_ed2k')
    except Exception:
        pass
    try:
        op.drop_column('resource_monitor_rules', 'target_path_magnet')
    except Exception:
        pass
    try:
        op.drop_column('resource_monitor_rules', 'target_path_pan115')
    except Exception:
        pass


