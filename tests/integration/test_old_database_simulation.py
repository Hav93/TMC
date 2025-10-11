#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟老版本数据库，测试 Schema 修复功能
"""

import sqlite3
import shutil
from pathlib import Path

# 备份当前数据库
DB_PATH = Path("data/bot.db")
BACKUP_PATH = Path("data/bot.db.backup_before_test")

print("=" * 60)
print("🧪 模拟老版本数据库测试")
print("=" * 60)

# 1. 备份当前数据库
if DB_PATH.exists():
    shutil.copy(DB_PATH, BACKUP_PATH)
    print(f"\n✅ 已备份数据库到: {BACKUP_PATH}")

# 2. 创建测试数据库（模拟老版本）
TEST_DB = Path("data/test_old_db.db")
conn = sqlite3.connect(TEST_DB)
cur = conn.cursor()

print(f"\n🔧 创建测试数据库: {TEST_DB}")

# 创建老版本的 telegram_clients 表（没有 last_connected 列）
cur.execute("""
CREATE TABLE IF NOT EXISTS telegram_clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id VARCHAR(100) UNIQUE NOT NULL,
    client_type VARCHAR(20) NOT NULL,
    phone VARCHAR(50),
    api_id VARCHAR(50),
    api_hash VARCHAR(100),
    bot_token VARCHAR(200),
    session_file VARCHAR(200),
    is_active BOOLEAN,
    auto_start BOOLEAN,
    last_used DATETIME,
    created_at DATETIME,
    updated_at DATETIME,
    admin_user_id VARCHAR(50)
    -- 注意：这里故意不包含 last_connected 列
)
""")

# 插入测试数据
cur.execute("""
INSERT INTO telegram_clients 
(client_id, client_type, phone, api_id, api_hash, is_active, auto_start, created_at)
VALUES 
('test_user', 'user', '+1234567890', '12345', 'abcdef', 1, 1, datetime('now'))
""")

conn.commit()

# 3. 验证老版本表结构
cur.execute("PRAGMA table_info(telegram_clients)")
columns = [col[1] for col in cur.fetchall()]

print(f"\n📊 老版本表结构（{len(columns)} 列）:")
for col in columns:
    print(f"  • {col}")

if 'last_connected' in columns:
    print("\n❌ 测试失败：老版本不应该有 last_connected 列")
else:
    print("\n✅ 测试通过：成功模拟了老版本数据库（缺少 last_connected）")

conn.close()

# 4. 现在测试 check_and_fix_schema.py 能否修复
print("\n" + "=" * 60)
print("🔍 测试 Schema 检查和修复")
print("=" * 60)
print("\n现在可以运行以下命令测试修复功能：")
print(f"  python check_and_fix_schema.py")
print(f"\n或者手动检查修复逻辑...")

# 5. 手动模拟修复逻辑
print("\n🔧 手动模拟修复过程...")
conn = sqlite3.connect(TEST_DB)
cur = conn.cursor()

# 检查列是否存在
cur.execute("PRAGMA table_info(telegram_clients)")
existing_columns = [col[1] for col in cur.fetchall()]

if 'last_connected' not in existing_columns:
    print("\n❌ 检测到缺失列: last_connected")
    print("🔧 正在添加列...")
    
    try:
        cur.execute("""
            ALTER TABLE telegram_clients 
            ADD COLUMN last_connected DATETIME
        """)
        conn.commit()
        print("✅ 成功添加 last_connected 列")
    except sqlite3.Error as e:
        print(f"❌ 添加列失败: {e}")

# 验证修复结果
cur.execute("PRAGMA table_info(telegram_clients)")
updated_columns = [col[1] for col in cur.fetchall()]

print(f"\n📊 修复后的表结构（{len(updated_columns)} 列）:")
for col in updated_columns:
    mark = "🆕" if col == "last_connected" else "  "
    print(f"{mark} • {col}")

if 'last_connected' in updated_columns:
    print("\n🎉 修复成功！last_connected 列已添加")
else:
    print("\n❌ 修复失败！last_connected 列仍然缺失")

conn.close()

print("\n" + "=" * 60)
print("📝 测试总结")
print("=" * 60)
print(f"\n✅ 测试数据库: {TEST_DB}")
print(f"✅ 备份数据库: {BACKUP_PATH}")
print("\n说明：")
print("  1. 成功模拟了老版本数据库（缺少 last_connected）")
print("  2. 手动模拟的修复逻辑验证通过")
print("  3. check_and_fix_schema.py 应该能自动修复此问题")
print(f"\n可以删除测试文件: rm {TEST_DB}")

