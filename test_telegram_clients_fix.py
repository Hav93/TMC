#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 telegram_clients 表的 Schema 修复
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/bot.db")

print("=" * 60)
print("🔍 检查 telegram_clients 表结构")
print("=" * 60)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 检查表是否存在
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='telegram_clients'")
table_exists = cur.fetchone()

if not table_exists:
    print("\n⚠️  telegram_clients 表不存在")
else:
    print("\n✅ telegram_clients 表存在")
    
    # 获取当前列
    cur.execute("PRAGMA table_info(telegram_clients)")
    columns = cur.fetchall()
    
    print(f"\n当前列数: {len(columns)}")
    print("\n当前列列表:")
    for col in columns:
        print(f"  • {col[1]:20s} {col[2]:15s} {'NOT NULL' if col[3] else 'NULL':10s}")
    
    # 检查 last_connected 列
    col_names = [col[1] for col in columns]
    if 'last_connected' in col_names:
        print("\n✅ last_connected 列存在")
    else:
        print("\n❌ last_connected 列缺失（这是用户报告的问题）")
        print("\n🔧 运行 check_and_fix_schema.py 应该会自动修复这个问题")

conn.close()

print("\n" + "=" * 60)

