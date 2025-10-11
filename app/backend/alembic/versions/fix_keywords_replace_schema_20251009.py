"""修复 keywords 和 replace_rules 表结构

Revision ID: fix_keywords_replace_schema_20251009
Revises: add_media_settings_20250108
Create Date: 2025-10-09 21:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'fix_keywords_replace_schema_20251009'
down_revision = 'add_media_settings_20250108'
branch_labels = None
depends_on = None


def upgrade():
    """
    修复 keywords 和 replace_rules 表结构
    
    keywords 表：
    - 添加 is_regex 列（如果不存在）
    - 添加 case_sensitive 列（如果不存在）
    - 删除 match_type 列（如果存在，已废弃）
    
    replace_rules 表：
    - 添加 name 列（如果不存在）
    - 添加 priority 列（如果不存在）
    - 添加 is_regex 列（如果不存在）
    - 添加 is_global 列（如果不存在）
    """
    
    # 获取数据库连接
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # ========== 修复 keywords 表 ==========
    print("\n=== 修复 keywords 表结构 ===")
    keywords_columns = {col['name'] for col in inspector.get_columns('keywords')}
    print(f"当前 keywords 列: {keywords_columns}")
    
    with op.batch_alter_table('keywords', schema=None) as batch_op:
        # 添加 is_regex 列
        if 'is_regex' not in keywords_columns:
            print("添加 keywords.is_regex")
            batch_op.add_column(
                sa.Column('is_regex', sa.Boolean(), nullable=True, comment='是否为正则表达式')
            )
            # 设置默认值
            conn.execute(sa.text("UPDATE keywords SET is_regex = 0 WHERE is_regex IS NULL"))
        
        # 添加 case_sensitive 列
        if 'case_sensitive' not in keywords_columns:
            print("添加 keywords.case_sensitive")
            batch_op.add_column(
                sa.Column('case_sensitive', sa.Boolean(), nullable=True, comment='是否区分大小写')
            )
            # 设置默认值
            conn.execute(sa.text("UPDATE keywords SET case_sensitive = 0 WHERE case_sensitive IS NULL"))
        
        # 删除废弃的 match_type 列
        if 'match_type' in keywords_columns:
            print("删除废弃的 keywords.match_type")
            batch_op.drop_column('match_type')
    
    # ========== 修复 replace_rules 表 ==========
    print("\n=== 修复 replace_rules 表结构 ===")
    replace_rules_columns = {col['name'] for col in inspector.get_columns('replace_rules')}
    print(f"当前 replace_rules 列: {replace_rules_columns}")
    
    with op.batch_alter_table('replace_rules', schema=None) as batch_op:
        # 添加 name 列
        if 'name' not in replace_rules_columns:
            print("添加 replace_rules.name")
            batch_op.add_column(
                sa.Column('name', sa.String(100), nullable=True, comment='替换规则名称')
            )
            # 为现有记录设置默认名称
            conn.execute(sa.text("UPDATE replace_rules SET name = '替换规则 #' || id WHERE name IS NULL"))
        
        # 添加 priority 列
        if 'priority' not in replace_rules_columns:
            print("添加 replace_rules.priority")
            batch_op.add_column(
                sa.Column('priority', sa.Integer(), nullable=True, comment='优先级，数字越小优先级越高')
            )
            # 设置默认值
            conn.execute(sa.text("UPDATE replace_rules SET priority = 0 WHERE priority IS NULL"))
        
        # 添加 is_regex 列
        if 'is_regex' not in replace_rules_columns:
            print("添加 replace_rules.is_regex")
            batch_op.add_column(
                sa.Column('is_regex', sa.Boolean(), nullable=True, comment='是否为正则表达式')
            )
            # 设置默认值为 True（向后兼容）
            conn.execute(sa.text("UPDATE replace_rules SET is_regex = 1 WHERE is_regex IS NULL"))
        
        # 添加 is_global 列
        if 'is_global' not in replace_rules_columns:
            print("添加 replace_rules.is_global")
            batch_op.add_column(
                sa.Column('is_global', sa.Boolean(), nullable=True, comment='是否全局替换')
            )
            # 设置默认值
            conn.execute(sa.text("UPDATE replace_rules SET is_global = 0 WHERE is_global IS NULL"))
    
    print("\n✅ 表结构修复完成")


def downgrade():
    """回滚迁移"""
    
    # 获取数据库连接
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # ========== 回滚 keywords 表 ==========
    keywords_columns = {col['name'] for col in inspector.get_columns('keywords')}
    
    with op.batch_alter_table('keywords', schema=None) as batch_op:
        # 恢复 match_type 列
        if 'match_type' not in keywords_columns:
            batch_op.add_column(
                sa.Column('match_type', sa.String(20), nullable=True)
            )
            # 根据 is_regex 设置 match_type
            conn.execute(sa.text(
                "UPDATE keywords SET match_type = CASE WHEN is_regex = 1 THEN 'regex' ELSE 'exact' END"
            ))
        
        # 删除新添加的列
        if 'is_regex' in keywords_columns:
            batch_op.drop_column('is_regex')
        if 'case_sensitive' in keywords_columns:
            batch_op.drop_column('case_sensitive')
    
    # ========== 回滚 replace_rules 表 ==========
    replace_rules_columns = {col['name'] for col in inspector.get_columns('replace_rules')}
    
    with op.batch_alter_table('replace_rules', schema=None) as batch_op:
        # 删除新添加的列
        if 'name' in replace_rules_columns:
            batch_op.drop_column('name')
        if 'priority' in replace_rules_columns:
            batch_op.drop_column('priority')
        if 'is_regex' in replace_rules_columns:
            batch_op.drop_column('is_regex')
        if 'is_global' in replace_rules_columns:
            batch_op.drop_column('is_global')

