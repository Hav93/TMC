#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建一个真正的老版本数据库（没有 last_connected）
"""

import sqlite3
from pathlib import Path

TEST_DB = Path("data/test_old_version.db")

# 删除旧的测试数据库
if TEST_DB.exists():
    TEST_DB.unlink()

print("🔧 创建老版本数据库（模拟用户报告的问题）")

conn = sqlite3.connect(TEST_DB)
cur = conn.cursor()

# 创建老版本的 telegram_clients 表（故意不包含 last_connected）
cur.execute("""
CREATE TABLE telegram_clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id VARCHAR(100) UNIQUE NOT NULL,
    client_type VARCHAR(20) NOT NULL,
    phone VARCHAR(50),
    api_id VARCHAR(50),
    api_hash VARCHAR(100),
    bot_token VARCHAR(200),
    is_active BOOLEAN,
    auto_start BOOLEAN,
    created_at DATETIME,
    updated_at DATETIME,
    admin_user_id VARCHAR(50)
)
""")

# 插入测试数据
cur.execute("""
INSERT INTO telegram_clients 
(client_id, client_type, is_active, auto_start, created_at)
VALUES 
('old_client', 'user', 1, 1, datetime('now'))
""")

conn.commit()

# 验证
cur.execute("PRAGMA table_info(telegram_clients)")
columns = [col[1] for col in cur.fetchall()]

print(f"\n✅ 创建成功，共 {len(columns)} 列:")
for col in columns:
    print(f"  • {col}")

if 'last_connected' not in columns:
    print(f"\n✅ 确认：缺少 'last_connected' 列（模拟用户问题）")
    print(f"\n💾 测试数据库路径: {TEST_DB}")
else:
    print(f"\n❌ 错误：不应该有 'last_connected' 列")

conn.close()

