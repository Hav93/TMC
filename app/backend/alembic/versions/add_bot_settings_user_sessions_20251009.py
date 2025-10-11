"""添加 bot_settings 和 user_sessions 表

Revision ID: add_bot_settings_user_sessions_20251009
Revises: fix_keywords_replace_schema_20251009
Create Date: 2025-10-09 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'add_bot_settings_user_sessions_20251009'
down_revision = 'fix_keywords_replace_schema_20251009'
branch_labels = None
depends_on = None


def upgrade():
    """
    添加 bot_settings 和 user_sessions 表
    """
    
    # 获取数据库连接
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()
    
    # ========== 创建 user_sessions 表 ==========
    if 'user_sessions' not in existing_tables:
        print("\n=== 创建 user_sessions 表 ===")
        op.create_table(
            'user_sessions',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
            sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
            sa.Column('username', sa.String(100), nullable=True, comment='用户名'),
            sa.Column('first_name', sa.String(100), nullable=True, comment='名字'),
            sa.Column('last_name', sa.String(100), nullable=True, comment='姓氏'),
            sa.Column('phone_number', sa.String(20), nullable=True, comment='手机号码'),
            sa.Column('is_admin', sa.Boolean(), nullable=True, comment='是否为管理员'),
            sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否活跃'),
            sa.Column('last_activity', sa.DateTime(), nullable=True, comment='最后活动时间'),
            sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )
        print("✅ user_sessions 表创建完成")
    else:
        print("\n⚠️  user_sessions 表已存在，跳过创建")
    
    # ========== 创建 bot_settings 表 ==========
    if 'bot_settings' not in existing_tables:
        print("\n=== 创建 bot_settings 表 ===")
        op.create_table(
            'bot_settings',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
            sa.Column('key', sa.String(100), nullable=False, comment='设置键'),
            sa.Column('value', sa.Text(), nullable=True, comment='设置值'),
            sa.Column('description', sa.String(500), nullable=True, comment='设置描述'),
            sa.Column('data_type', sa.String(20), nullable=True, comment='数据类型'),
            sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否为系统设置'),
            sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('key')
        )
        print("✅ bot_settings 表创建完成")
        
        # 插入默认设置
        print("\n=== 插入默认设置 ===")
        from datetime import datetime
        default_settings = [
            {
                'key': 'max_forward_delay',
                'value': '5',
                'description': '最大转发延迟(秒)',
                'data_type': 'integer',
                'is_system': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'key': 'enable_auto_retry',
                'value': 'true',
                'description': '启用自动重试',
                'data_type': 'boolean',
                'is_system': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'key': 'max_retry_count',
                'value': '3',
                'description': '最大重试次数',
                'data_type': 'integer',
                'is_system': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
        ]
        
        for setting in default_settings:
            try:
                conn.execute(
                    sa.text(
                        "INSERT INTO bot_settings (key, value, description, data_type, is_system, created_at, updated_at) "
                        "VALUES (:key, :value, :description, :data_type, :is_system, :created_at, :updated_at)"
                    ),
                    setting
                )
                print(f"  ✅ 插入默认设置: {setting['key']}")
            except Exception as e:
                print(f"  ⚠️  插入设置失败: {setting['key']} - {e}")
        
        print("✅ 默认设置插入完成")
    else:
        print("\n⚠️  bot_settings 表已存在，跳过创建")
    
    print("\n✅ 迁移完成")


def downgrade():
    """回滚迁移"""
    
    # 获取数据库连接
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()
    
    # 删除 bot_settings 表
    if 'bot_settings' in existing_tables:
        print("\n=== 删除 bot_settings 表 ===")
        op.drop_table('bot_settings')
        print("✅ bot_settings 表已删除")
    
    # 删除 user_sessions 表
    if 'user_sessions' in existing_tables:
        print("\n=== 删除 user_sessions 表 ===")
        op.drop_table('user_sessions')
        print("✅ user_sessions 表已删除")
    
    print("\n✅ 回滚完成")

