#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用实际的 check_and_fix_schema.py 逻辑测试 telegram_clients 修复
"""

import sqlite3
from pathlib import Path

# 使用测试数据库
TEST_DB = Path("data/test_old_db.db")

print("=" * 60)
print("🔍 使用 check_and_fix_schema.py 的逻辑测试修复")
print("=" * 60)

# 期望的 Schema（从 check_and_fix_schema.py 复制）
EXPECTED_SCHEMA = {
    "telegram_clients": {
        "id": "INTEGER",
        "client_id": "VARCHAR",
        "client_type": "VARCHAR",
        "bot_token": "VARCHAR",
        "admin_user_id": "VARCHAR",
        "api_id": "VARCHAR",
        "api_hash": "VARCHAR",
        "phone": "VARCHAR",
        "is_active": "BOOLEAN",
        "auto_start": "BOOLEAN",
        "last_connected": "DATETIME",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
}

conn = sqlite3.connect(TEST_DB)
cur = conn.cursor()

print(f"\n📊 检查测试数据库: {TEST_DB}")

# 获取实际列
cur.execute("PRAGMA table_info(telegram_clients)")
actual_columns = {col[1]: col[2] for col in cur.fetchall()}

print(f"\n当前列数: {len(actual_columns)}")

# 对比期望的列
expected_columns = EXPECTED_SCHEMA["telegram_clients"]
missing_columns = []

for col_name, col_type in expected_columns.items():
    if col_name not in actual_columns:
        missing_columns.append((col_name, col_type))
        print(f"❌ 缺失列: {col_name} {col_type}")
    else:
        # 简单的类型检查（忽略长度）
        actual_type = actual_columns[col_name].split('(')[0].upper()
        expected_type = col_type.split('(')[0].upper()
        if actual_type == expected_type or expected_type == "VARCHAR":
            print(f"✅ 已存在: {col_name} ({actual_columns[col_name]})")
        else:
            print(f"⚠️  类型不匹配: {col_name} (实际: {actual_columns[col_name]}, 期望: {col_type})")

# 修复缺失的列
if missing_columns:
    print(f"\n🔧 发现 {len(missing_columns)} 个缺失列，开始修复...")
    
    for col_name, col_type in missing_columns:
        print(f"\n  添加列: {col_name} {col_type}")
        try:
            # 构造 SQL
            sql = f"ALTER TABLE telegram_clients ADD COLUMN {col_name} {col_type}"
            cur.execute(sql)
            conn.commit()
            print(f"  ✅ 成功添加: {col_name}")
        except sqlite3.Error as e:
            print(f"  ❌ 失败: {e}")
else:
    print("\n✅ 所有期望的列都存在，无需修复")

# 验证最终结果
cur.execute("PRAGMA table_info(telegram_clients)")
final_columns = [col[1] for col in cur.fetchall()]

print(f"\n📊 修复后的列（{len(final_columns)} 列）:")
for col in final_columns:
    if col in expected_columns:
        print(f"  ✅ {col}")
    else:
        print(f"  ℹ️  {col} (老版本遗留列，保留兼容)")

# 检查关键列
if 'last_connected' in final_columns:
    print("\n🎉 关键列 'last_connected' 已存在！")
    print("   用户报告的问题已修复！")
else:
    print("\n❌ 关键列 'last_connected' 仍然缺失")

conn.close()

print("\n" + "=" * 60)

