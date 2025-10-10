#!/usr/bin/env python3
"""
数据库Schema智能检测和修复工具

策略：
1. 检查数据库中实际的表结构
2. 对比模型定义（models.py）
3. 自动修复缺失的列（不删除多余的列，保证安全）
4. 记录所有变更以便追踪

这个脚本作为 Alembic 迁移的补充，处理以下场景：
- 用户从非常老的版本升级
- 用户手动修改了数据库
- Alembic 迁移历史不完整
"""

import sqlite3
import sys
from typing import Dict, List, Set
from pathlib import Path

# 数据库路径（相对于工作目录 /app）
DB_PATH = Path("data/bot.db")

# 预期的表结构（基于 models.py）
EXPECTED_SCHEMA = {
    "forward_rules": {
        "id": "INTEGER",
        "name": "VARCHAR",
        "source_chat_id": "VARCHAR",
        "source_chat_name": "VARCHAR",
        "target_chat_id": "VARCHAR",
        "target_chat_name": "VARCHAR",
        "is_active": "BOOLEAN",
        "enable_keyword_filter": "BOOLEAN",
        "enable_regex_replace": "BOOLEAN",
        "client_id": "VARCHAR",
        "client_type": "VARCHAR",
        "enable_text": "BOOLEAN",
        "enable_media": "BOOLEAN",
        "enable_photo": "BOOLEAN",
        "enable_video": "BOOLEAN",
        "enable_document": "BOOLEAN",
        "enable_audio": "BOOLEAN",
        "enable_voice": "BOOLEAN",
        "enable_sticker": "BOOLEAN",
        "enable_animation": "BOOLEAN",
        "enable_webpage": "BOOLEAN",
        "forward_delay": "INTEGER",
        "max_message_length": "INTEGER",
        "enable_link_preview": "BOOLEAN",
        "time_filter_type": "VARCHAR",
        "start_time": "DATETIME",
        "end_time": "DATETIME",
        "enable_deduplication": "BOOLEAN",
        "dedup_time_window": "INTEGER",
        "dedup_check_content": "BOOLEAN",
        "dedup_check_media": "BOOLEAN",
        "enable_sender_filter": "BOOLEAN",
        "sender_filter_mode": "VARCHAR",
        "sender_whitelist": "TEXT",
        "sender_blacklist": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "keywords": {
        "id": "INTEGER",
        "rule_id": "INTEGER",
        "keyword": "VARCHAR(500)",
        "is_regex": "BOOLEAN",
        "is_exclude": "BOOLEAN",
        "case_sensitive": "BOOLEAN",
        "created_at": "DATETIME",
    },
    "replace_rules": {
        "id": "INTEGER",
        "rule_id": "INTEGER",
        "name": "VARCHAR(100)",
        "pattern": "TEXT",
        "replacement": "TEXT",
        "priority": "INTEGER",
        "is_regex": "BOOLEAN",
        "is_active": "BOOLEAN",
        "is_global": "BOOLEAN",
        "created_at": "DATETIME",
    },
    "message_logs": {
        "id": "INTEGER",
        "rule_id": "INTEGER",
        "rule_name": "VARCHAR(100)",
        "source_chat_id": "VARCHAR(50)",
        "source_chat_name": "VARCHAR(200)",
        "source_message_id": "INTEGER",
        "target_chat_id": "VARCHAR(50)",
        "target_chat_name": "VARCHAR(200)",
        "target_message_id": "INTEGER",
        "original_text": "TEXT",
        "processed_text": "TEXT",
        "media_type": "VARCHAR(50)",
        "content_hash": "VARCHAR(64)",
        "media_hash": "VARCHAR(64)",
        "sender_id": "VARCHAR(50)",
        "sender_username": "VARCHAR(100)",
        "status": "VARCHAR(20)",
        "error_message": "TEXT",
        "processing_time": "INTEGER",
        "created_at": "DATETIME",
    },
    "user_sessions": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "username": "VARCHAR(100)",
        "first_name": "VARCHAR(100)",
        "last_name": "VARCHAR(100)",
        "phone_number": "VARCHAR(20)",
        "is_admin": "BOOLEAN",
        "is_active": "BOOLEAN",
        "last_activity": "DATETIME",
        "created_at": "DATETIME",
    },
    "bot_settings": {
        "id": "INTEGER",
        "key": "VARCHAR(100)",
        "value": "TEXT",
        "description": "VARCHAR(500)",
        "data_type": "VARCHAR(20)",
        "is_system": "BOOLEAN",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "telegram_clients": {
        "id": "INTEGER",
        "client_id": "VARCHAR",  # 兼容不同长度
        "client_type": "VARCHAR",
        "bot_token": "VARCHAR",
        "admin_user_id": "VARCHAR",
        "api_id": "VARCHAR",
        "api_hash": "VARCHAR",
        "phone": "VARCHAR",
        "is_active": "BOOLEAN",
        "auto_start": "BOOLEAN",
        "last_connected": "DATETIME",  # 关键列，用户报告缺失
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
        # 注意：session_file 和 last_used 是老版本的列，新版本不需要，但保留兼容
    },
}

# 废弃的列（需要删除，但为了安全暂不删除，只记录）
DEPRECATED_COLUMNS = {
    "keywords": ["match_type"],
}


def get_table_columns(conn: sqlite3.Connection, table_name: str) -> Dict[str, str]:
    """获取表的实际列结构"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {}
    for row in cursor.fetchall():
        col_name = row[1]
        col_type = row[2]
        columns[col_name] = col_type
    return columns


def add_missing_column(
    conn: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_type: str,
    default_value=None,
):
    """添加缺失的列"""
    cursor = conn.cursor()
    
    # 确定默认值
    if default_value is None:
        if "BOOLEAN" in column_type.upper():
            default_value = 0
        elif "INTEGER" in column_type.upper():
            default_value = 0
        elif "TEXT" in column_type.upper() or "VARCHAR" in column_type.upper():
            default_value = "''"
    
    try:
        # 添加列
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        if default_value is not None:
            sql += f" DEFAULT {default_value}"
        
        print(f"  ➕ 添加列: {table_name}.{column_name} ({column_type})")
        cursor.execute(sql)
        conn.commit()
        
        # 如果是布尔类型，设置默认值
        if "BOOLEAN" in column_type.upper() and default_value == 0:
            cursor.execute(
                f"UPDATE {table_name} SET {column_name} = 0 WHERE {column_name} IS NULL"
            )
            conn.commit()
        
        return True
    except sqlite3.OperationalError as e:
        print(f"  ⚠️  无法添加列 {table_name}.{column_name}: {e}")
        return False


def check_and_fix_table(
    conn: sqlite3.Connection, table_name: str, expected_columns: Dict[str, str]
) -> bool:
    """检查并修复单个表"""
    if not expected_columns:
        return True  # 跳过未定义的表
    
    print(f"\n🔍 检查表: {table_name}")
    
    # 检查表是否存在
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    )
    if not cursor.fetchone():
        print(f"  ⚠️  表不存在（将由 Alembic 创建）")
        return True
    
    # 获取实际列
    actual_columns = get_table_columns(conn, table_name)
    print(f"  📋 当前列: {list(actual_columns.keys())}")
    
    # 检查缺失的列
    missing_columns = set(expected_columns.keys()) - set(actual_columns.keys())
    if missing_columns:
        print(f"  ❌ 缺失的列: {missing_columns}")
        for col_name in missing_columns:
            col_type = expected_columns[col_name]
            add_missing_column(conn, table_name, col_name, col_type)
    else:
        print(f"  ✅ 所有必需的列都存在")
    
    # 检查废弃的列（但不删除）
    if table_name in DEPRECATED_COLUMNS:
        deprecated = set(DEPRECATED_COLUMNS[table_name]) & set(actual_columns.keys())
        if deprecated:
            print(f"  📝 发现废弃的列（保留但不使用）: {deprecated}")
    
    # 检查多余的列（记录但不删除，保证安全）
    extra_columns = set(actual_columns.keys()) - set(expected_columns.keys())
    if table_name in DEPRECATED_COLUMNS:
        extra_columns -= set(DEPRECATED_COLUMNS[table_name])
    if extra_columns:
        print(f"  ℹ️  额外的列（可能来自旧版本）: {extra_columns}")
    
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("🔍 数据库Schema智能检测和修复")
    print("=" * 60)
    
    # 检查数据库文件是否存在
    if not DB_PATH.exists():
        print(f"📝 数据库文件不存在: {DB_PATH}")
        print("✅ 新安装，Alembic 将创建完整的数据库结构")
        return 0
    
    print(f"📊 数据库路径: {DB_PATH}")
    
    try:
        # 连接数据库
        conn = sqlite3.connect(str(DB_PATH))
        
        # 检查并修复每个表
        all_ok = True
        for table_name, expected_columns in EXPECTED_SCHEMA.items():
            if not check_and_fix_table(conn, table_name, expected_columns):
                all_ok = False
        
        conn.close()
        
        print("\n" + "=" * 60)
        if all_ok:
            print("✅ 数据库Schema检查完成")
        else:
            print("⚠️  数据库Schema检查完成（有警告）")
        print("=" * 60)
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Schema检查失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

