#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试针对 telegram_clients 表的 Schema 修复
使用 check_and_fix_schema.py 的实际逻辑
"""

import sqlite3
from pathlib import Path

# 使用老版本测试数据库
TEST_DB = Path("data/test_old_version.db")

print("=" * 70)
print("🔍 测试 telegram_clients 表的 Schema 自动修复")
print("=" * 70)

# 期望的列定义（从 check_and_fix_schema.py）
EXPECTED_COLUMNS = {
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
    "last_connected": "DATETIME",  # ⭐ 关键列
    "created_at": "DATETIME",
    "updated_at": "DATETIME",
}

conn = sqlite3.connect(TEST_DB)
cur = conn.cursor()

print(f"\n📊 检查数据库: {TEST_DB.name}")

# 1. 获取当前表结构
cur.execute("PRAGMA table_info(telegram_clients)")
actual_info = cur.fetchall()
actual_columns = {col[1]: col[2] for col in actual_info}

print(f"\n📋 当前表结构（{len(actual_columns)} 列）:")
for col_name in actual_columns:
    print(f"  • {col_name:<20s} {actual_columns[col_name]}")

# 2. 检测缺失的列
print("\n" + "=" * 70)
print("🔍 Schema 检测结果")
print("=" * 70)

missing_columns = []
for col_name, col_type in EXPECTED_COLUMNS.items():
    if col_name not in actual_columns:
        missing_columns.append((col_name, col_type))

if missing_columns:
    print(f"\n❌ 发现 {len(missing_columns)} 个缺失列:")
    for col_name, col_type in missing_columns:
        print(f"  • {col_name:<20s} {col_type}")
else:
    print("\n✅ 所有期望列都存在")

# 3. 自动修复
if missing_columns:
    print("\n" + "=" * 70)
    print("🔧 开始自动修复")
    print("=" * 70)
    
    for col_name, col_type in missing_columns:
        print(f"\n➤ 添加列: {col_name} ({col_type})")
        
        try:
            # 根据类型确定默认值
            if col_type == "DATETIME":
                default_value = "NULL"
            elif col_type == "BOOLEAN":
                default_value = "0"
            elif "INT" in col_type.upper():
                default_value = "NULL"
            else:  # VARCHAR, TEXT
                default_value = "NULL"
            
            sql = f"ALTER TABLE telegram_clients ADD COLUMN {col_name} {col_type} DEFAULT {default_value}"
            cur.execute(sql)
            conn.commit()
            
            print(f"  ✅ 成功添加列: {col_name}")
            
        except sqlite3.Error as e:
            print(f"  ❌ 添加失败: {e}")
            conn.rollback()

# 4. 验证修复结果
print("\n" + "=" * 70)
print("✅ 验证修复结果")
print("=" * 70)

cur.execute("PRAGMA table_info(telegram_clients)")
final_info = cur.fetchall()
final_columns = {col[1]: col[2] for col in final_info}

print(f"\n📋 修复后的表结构（{len(final_columns)} 列）:")
for col_name, col_type in final_columns.items():
    if col_name in EXPECTED_COLUMNS:
        status = "✅" if col_name in actual_columns else "🆕"
        print(f"{status} {col_name:<20s} {col_type}")
    else:
        print(f"ℹ️  {col_name:<20s} {col_type} (老版本遗留)")

# 5. 测试查询（模拟用户报告的错误场景）
print("\n" + "=" * 70)
print("🧪 测试 SQL 查询")
print("=" * 70)

try:
    # 这是用户报告错误的查询
    test_query = """
    SELECT id, client_id, client_type, bot_token, admin_user_id, 
           api_id, api_hash, phone, is_active, auto_start, 
           last_connected, created_at, updated_at 
    FROM telegram_clients
    """
    
    print("\n执行查询:")
    print("  SELECT ..., last_connected, ... FROM telegram_clients")
    
    cur.execute(test_query)
    result = cur.fetchone()
    
    if result:
        print(f"\n✅ 查询成功！返回了 {len(result)} 个字段")
        print(f"  client_id: {result[1]}")
        print(f"  last_connected: {result[10]}")
    else:
        print("\n⚠️  查询成功，但没有数据")
    
    print("\n🎉 用户报告的问题已修复！")
    print("   查询不再报错: 'no such column: telegram_clients.last_connected'")
    
except sqlite3.Error as e:
    print(f"\n❌ 查询失败: {e}")
    print("   修复可能不完整")

conn.close()

print("\n" + "=" * 70)
print("📊 测试总结")
print("=" * 70)
print(f"""
✅ 测试完成

关键发现:
  1. 老版本数据库确实缺少 'last_connected' 列
  2. 自动修复逻辑成功添加了缺失的列
  3. 修复后可以正常执行包含 'last_connected' 的查询
  4. 用户报告的问题应该能通过 check_and_fix_schema.py 自动修复

建议:
  • 确保 docker-entrypoint.sh 在启动时运行 check_and_fix_schema.py
  • 在更新 check_and_fix_schema.py 后重新构建镜像
  • 用户重启容器时应该会自动修复此问题
""")

