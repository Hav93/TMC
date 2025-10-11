#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证所有表是否存在
"""

import sqlite3

conn = sqlite3.connect('data/bot.db')
cur = conn.cursor()

# 查询所有表
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cur.fetchall()]

print("=" * 60)
print("📊 数据库表列表")
print("=" * 60)
print(f"\n总共 {len(tables)} 个表:\n")

for i, table in enumerate(tables, 1):
    # 查询每个表的记录数
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    
    # 查询表的列数
    cur.execute(f"PRAGMA table_info({table})")
    cols = cur.fetchall()
    
    print(f"{i:2d}. {table:25s} - {count:4d} 行, {len(cols):2d} 列")

# 检查 Alembic 版本
print("\n" + "=" * 60)
print("📋 Alembic 迁移版本")
print("=" * 60)
cur.execute("SELECT version_num FROM alembic_version")
version = cur.fetchone()
if version:
    print(f"\n当前版本: {version[0]}")
else:
    print("\n⚠️  未找到版本记录")

# 检查 bot_settings 默认设置
print("\n" + "=" * 60)
print("⚙️  Bot Settings 默认配置")
print("=" * 60)
cur.execute("SELECT key, value, description FROM bot_settings ORDER BY key")
settings = cur.fetchall()
if settings:
    print()
    for setting in settings:
        print(f"  • {setting[0]:20s} = {setting[1]:10s} ({setting[2]})")
else:
    print("\n⚠️  未找到默认设置")

conn.close()

print("\n" + "=" * 60)
print("✅ 验证完成")
print("=" * 60)

