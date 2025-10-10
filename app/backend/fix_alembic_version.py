#!/usr/bin/env python3
"""
智能数据库版本同步脚本

功能：
1. 检测数据库当前状态（表、字段）
2. 自动判断对应的 Alembic 版本
3. 创建/更新 alembic_version 表
4. 确保后续迁移能够正常增量执行

使用场景：
- 首次部署（空数据库）：标记为最新版本
- 已有数据库（无版本记录）：智能检测当前版本
- 版本不一致：修正为正确版本
"""
import sqlite3
import sys
import os
from pathlib import Path

DB_PATH = "data/bot.db"
LATEST_REVISION = "20250108_add_media_settings"  # 最新的迁移版本

# 版本检测规则（按时间倒序）
VERSION_RULES = [
    {
        "version": "20250108_add_media_settings",
        "check": lambda c: check_table_exists(c, "media_settings"),
        "desc": "媒体管理全局配置"
    },
    {
        "version": "20250108_add_last_connected",
        "check": lambda c: check_column_exists(c, "telegram_clients", "last_connected"),
        "desc": "客户端最后连接时间"
    },
    {
        "version": "20250108_add_media_management",
        "check": lambda c: (
            check_table_exists(c, "media_monitor_rules") and
            check_table_exists(c, "download_tasks") and
            check_table_exists(c, "media_files")
        ),
        "desc": "媒体文件管理"
    },
    {
        "version": "20251008_140419",
        "check": lambda c: (
            check_column_exists(c, "forward_rules", "enable_deduplication") and
            check_column_exists(c, "message_logs", "content_hash")
        ),
        "desc": "消息去重和发送者过滤"
    },
    {
        "version": "20251007_add_missing_fields",
        "check": lambda c: check_column_exists(c, "forward_rules", "enable_text"),
        "desc": "转发规则字段补全"
    },
    {
        "version": "20251006_add_avatar",
        "check": lambda c: check_column_exists(c, "users", "avatar"),
        "desc": "用户头像字段"
    },
    {
        "version": "20251006_add_users",
        "check": lambda c: check_table_exists(c, "users"),
        "desc": "用户表"
    },
    {
        "version": "001",
        "check": lambda c: check_table_exists(c, "forward_rules"),
        "desc": "基础表结构"
    },
]


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


def detect_database_version(cursor):
    """智能检测数据库当前版本"""
    for rule in VERSION_RULES:
        try:
            if rule["check"](cursor):
                return rule["version"], rule["desc"]
        except Exception as e:
            # 检查失败说明该版本的特征不存在，继续检查下一个
            continue
    
    return None, "空数据库"


def main():
    print("🔍 开始检查数据库版本...")
    
    # 如果数据库文件不存在，说明是首次启动
    if not os.path.exists(DB_PATH):
        print(f"📝 数据库文件不存在，将由 Alembic 创建: {DB_PATH}")
        print("✅ 跳过版本检查（首次启动）")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检测当前数据库版本
        detected_version, desc = detect_database_version(cursor)
        
        if detected_version is None:
            print("⚠️  数据库为空或缺少关键表")
            print("   Alembic 将创建所有表")
            # 不设置版本，让 Alembic 从头开始
            return
        
        print(f"📊 检测到数据库版本: {detected_version} ({desc})")
        
        # 创建 alembic_version 表
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, PRIMARY KEY (version_num))"
        )
        
        # 检查当前记录的版本
        cursor.execute("SELECT version_num FROM alembic_version LIMIT 1")
        current_record = cursor.fetchone()
        
        if current_record:
            current_version = current_record[0]
            if current_version == detected_version:
                print(f"✅ Alembic 版本记录正确: {current_version}")
                return
            else:
                print(f"⚠️  版本不一致！")
                print(f"   记录版本: {current_version}")
                print(f"   实际版本: {detected_version}")
                print(f"   正在修正...")
        
        # 更新版本记录
        cursor.execute("DELETE FROM alembic_version")
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES (?)", (detected_version,))
        conn.commit()
        
        print(f"✅ 已标记 Alembic 版本为: {detected_version}")
        
        if detected_version != LATEST_REVISION:
            print(f"📦 后续将自动应用迁移: {detected_version} -> {LATEST_REVISION}")

    except Exception as e:
        print(f"❌ 版本检查失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        # 不退出，让 Alembic 尝试处理
    finally:
        conn.close()


if __name__ == "__main__":
    main()
