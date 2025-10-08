#!/usr/bin/env python3
"""
修复 Alembic 版本记录

当数据库已经通过 SQLAlchemy 的 create_all() 创建，但缺少 Alembic 版本记录时使用此脚本。
此脚本会检查数据库表结构，并将 Alembic 版本标记为最新。
"""
import sqlite3
import sys
import os

DB_PATH = "data/bot.db"
LATEST_REVISION = "20251008_140419"  # 最新的迁移版本


def check_table_exists(cursor, table_name):
    """检查表是否存在"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def check_column_exists(cursor, table_name, column_name):
    """检查列是否存在"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检查关键表是否存在
        required_tables = ["forward_rules", "telegram_client", "message_logs"]
        missing_tables = [t for t in required_tables if not check_table_exists(cursor, t)]
        
        if missing_tables:
            print(f"❌ 数据库缺少必要的表: {missing_tables}")
            print("   请使用全新的数据库或运行完整迁移")
            sys.exit(1)

        # 检查新字段是否已存在
        new_columns = {
            "forward_rules": ["enable_deduplication", "enable_sender_filter"],
            "message_logs": ["content_hash", "sender_id"]
        }
        
        all_columns_exist = True
        for table, columns in new_columns.items():
            for column in columns:
                if not check_column_exists(cursor, table, column):
                    print(f"⚠️  表 {table} 缺少列: {column}")
                    all_columns_exist = False

        if all_columns_exist:
            print("✅ 数据库已包含所有新字段，无需迁移")
            # 直接标记为最新版本
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, PRIMARY KEY (version_num))"
            )
            cursor.execute("DELETE FROM alembic_version")
            cursor.execute("INSERT INTO alembic_version (version_num) VALUES (?)", (LATEST_REVISION,))
            conn.commit()
            print(f"✅ 已标记 Alembic 版本为: {LATEST_REVISION}")
            return

        # 如果字段不存在，需要运行迁移
        print("⚠️  数据库需要迁移，但表已存在")
        print("   解决方案：")
        print("   1. 创建 alembic_version 表并标记为基础版本")
        
        # 创建 alembic_version 表
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, PRIMARY KEY (version_num))"
        )
        
        # 检查当前应该标记为哪个版本
        # 如果 forward_rules 有 enable_text 等字段，说明至少到了 20251007
        if check_column_exists(cursor, "forward_rules", "enable_text"):
            base_version = "20251007_add_missing_fields"
            print(f"   检测到数据库版本: {base_version}")
        elif check_column_exists(cursor, "users", "avatar"):
            base_version = "20251006_add_avatar"
            print(f"   检测到数据库版本: {base_version}")
        elif check_table_exists(cursor, "users"):
            base_version = "20251006_add_users"
            print(f"   检测到数据库版本: {base_version}")
        else:
            base_version = "001"  # 初始版本
            print(f"   检测到数据库版本: {base_version}")
        
        cursor.execute("DELETE FROM alembic_version")
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES (?)", (base_version,))
        conn.commit()
        
        print(f"✅ 已标记 Alembic 版本为: {base_version}")
        print(f"   现在可以运行 'alembic upgrade head' 来应用剩余的迁移")

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
