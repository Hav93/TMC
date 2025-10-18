#!/usr/bin/env python3
"""
数据库表结构快速修复脚本
直接在容器中运行，无需等待 GitHub Actions 构建
"""
import sqlite3
import sys
from pathlib import Path

# 数据库文件路径
DB_PATH = Path("/app/data/bot.db")

def check_column_exists(cursor, table_name, column_name):
    """检查列是否存在"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def add_column_if_not_exists(cursor, table_name, column_name, column_def):
    """如果列不存在则添加"""
    if not check_column_exists(cursor, table_name, column_name):
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
            print(f"✅ 添加 {table_name}.{column_name}")
            return True
        except Exception as e:
            print(f"❌ 添加 {table_name}.{column_name} 失败: {e}")
            return False
    else:
        print(f"⏭️  {table_name}.{column_name} 已存在")
        return False

def rename_column_if_exists(conn, cursor, table_name, old_name, new_name):
    """如果旧列存在且新列不存在，则重命名"""
    has_old = check_column_exists(cursor, table_name, old_name)
    has_new = check_column_exists(cursor, table_name, new_name)
    
    if has_old and not has_new:
        try:
            cursor.execute(f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}")
            print(f"✅ 重命名 {table_name}.{old_name} -> {new_name}")
            return True
        except Exception as e:
            print(f"❌ 重命名失败: {e}")
            return False
    elif has_new:
        print(f"⏭️  {table_name}.{new_name} 已存在")
        return False
    else:
        print(f"⚠️  {table_name}.{old_name} 不存在，跳过重命名")
        return False

def main():
    print("=" * 60)
    print("数据库表结构修复工具")
    print("=" * 60)
    
    if not DB_PATH.exists():
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        sys.exit(1)
    
    print(f"📂 数据库路径: {DB_PATH}")
    print()
    
    # 连接数据库
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        changes_made = 0
        
        # 1. 修复 keywords 表
        print("🔧 修复 keywords 表...")
        if add_column_if_not_exists(cursor, "keywords", "is_exclude", 
                                    "BOOLEAN DEFAULT 0"):
            changes_made += 1
        if add_column_if_not_exists(cursor, "keywords", "case_sensitive", 
                                    "BOOLEAN DEFAULT 0"):
            changes_made += 1
        print()
        
        # 2. 修复 message_logs 表
        print("🔧 修复 message_logs 表...")
        
        # 重命名字段
        if rename_column_if_exists(conn, cursor, "message_logs", 
                                  "original_message_id", "source_message_id"):
            changes_made += 1
        if rename_column_if_exists(conn, cursor, "message_logs", 
                                  "forwarded_message_id", "target_message_id"):
            changes_made += 1
        
        # 添加缺失字段
        fields_to_add = [
            ("media_type", "VARCHAR(50)"),
            ("content_hash", "VARCHAR(64)"),
            ("media_hash", "VARCHAR(64)"),
            ("sender_id", "VARCHAR(50)"),
            ("sender_username", "VARCHAR(100)"),
            ("status", "VARCHAR(20) DEFAULT 'success'"),
            ("error_message", "TEXT"),
            ("processing_time", "REAL"),
        ]
        
        for field_name, field_def in fields_to_add:
            if add_column_if_not_exists(cursor, "message_logs", field_name, field_def):
                changes_made += 1
        print()
        
        # 3. 修复 replace_rules 表
        print("🔧 修复 replace_rules 表...")
        replace_fields = [
            ("name", "VARCHAR(100)"),
            ("is_active", "BOOLEAN DEFAULT 1"),
            ("is_global", "BOOLEAN DEFAULT 0"),
        ]
        
        for field_name, field_def in replace_fields:
            if add_column_if_not_exists(cursor, "replace_rules", field_name, field_def):
                changes_made += 1
        print()
        
        # 提交更改
        conn.commit()
        
        print("=" * 60)
        if changes_made > 0:
            print(f"✅ 完成！共修复 {changes_made} 个字段")
            print("🔄 请重启应用以生效")
        else:
            print("✅ 数据库表结构已是最新，无需修复")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 修复过程出错: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()

