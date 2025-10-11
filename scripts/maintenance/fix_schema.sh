#!/bin/bash
cd /app

python3 << 'PYTHON_SCRIPT'
import sqlite3

conn = sqlite3.connect('data/bot.db')
cur = conn.cursor()

# 修复 keywords 表
print('📋 修复 keywords 表...')
cur.execute('PRAGMA table_info(keywords)')
cols = {row[1] for row in cur.fetchall()}
print(f'  当前列: {list(cols)}')

if 'is_regex' not in cols:
    print('  ➕ 添加 is_regex')
    cur.execute('ALTER TABLE keywords ADD COLUMN is_regex BOOLEAN DEFAULT 0')
else:
    print('  ✅ is_regex 已存在')
    
if 'case_sensitive' not in cols:
    print('  ➕ 添加 case_sensitive')
    cur.execute('ALTER TABLE keywords ADD COLUMN case_sensitive BOOLEAN DEFAULT 0')
else:
    print('  ✅ case_sensitive 已存在')

# 修复 replace_rules 表
print('\n📋 修复 replace_rules 表...')
cur.execute('PRAGMA table_info(replace_rules)')
cols = {row[1] for row in cur.fetchall()}
print(f'  当前列: {list(cols)}')

if 'name' not in cols:
    print('  ➕ 添加 name')
    cur.execute('ALTER TABLE replace_rules ADD COLUMN name VARCHAR(100)')
else:
    print('  ✅ name 已存在')
    
if 'priority' not in cols:
    print('  ➕ 添加 priority')
    cur.execute('ALTER TABLE replace_rules ADD COLUMN priority INTEGER DEFAULT 0')
else:
    print('  ✅ priority 已存在')
    
if 'is_regex' not in cols:
    print('  ➕ 添加 is_regex')
    cur.execute('ALTER TABLE replace_rules ADD COLUMN is_regex BOOLEAN DEFAULT 1')
else:
    print('  ✅ is_regex 已存在')
    
if 'is_global' not in cols:
    print('  ➕ 添加 is_global')
    cur.execute('ALTER TABLE replace_rules ADD COLUMN is_global BOOLEAN DEFAULT 0')
else:
    print('  ✅ is_global 已存在')

conn.commit()
conn.close()
print('\n✅ Schema修复完成！')
PYTHON_SCRIPT

