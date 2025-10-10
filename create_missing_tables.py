#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建缺失的 bot_settings 和 user_sessions 表
"""

import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/bot.db')
cur = conn.cursor()

# 检查现有表
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
existing_tables = {row[0] for row in cur.fetchall()}
print(f"现有表: {existing_tables}")

# ========== 创建 user_sessions 表 ==========
if 'user_sessions' not in existing_tables:
    print('\n📋 创建 user_sessions 表...')
    cur.execute('''
        CREATE TABLE user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            username VARCHAR(100),
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            phone_number VARCHAR(20),
            is_admin BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            last_activity DATETIME,
            created_at DATETIME
        )
    ''')
    print('✅ user_sessions 表创建完成')
else:
    print('\n⚠️  user_sessions 表已存在')

# ========== 创建 bot_settings 表 ==========
if 'bot_settings' not in existing_tables:
    print('\n📋 创建 bot_settings 表...')
    cur.execute('''
        CREATE TABLE bot_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key VARCHAR(100) NOT NULL UNIQUE,
            value TEXT,
            description VARCHAR(500),
            data_type VARCHAR(20) DEFAULT 'string',
            is_system BOOLEAN DEFAULT 0,
            created_at DATETIME,
            updated_at DATETIME
        )
    ''')
    print('✅ bot_settings 表创建完成')
    
    # 插入默认设置
    print('\n📋 插入默认设置...')
    now = datetime.now().isoformat()
    default_settings = [
        ('max_forward_delay', '5', '最大转发延迟(秒)', 'integer', 1, now, now),
        ('enable_auto_retry', 'true', '启用自动重试', 'boolean', 1, now, now),
        ('max_retry_count', '3', '最大重试次数', 'integer', 1, now, now),
    ]
    
    for setting in default_settings:
        cur.execute('''
            INSERT INTO bot_settings (key, value, description, data_type, is_system, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', setting)
        print(f'  ✅ 插入默认设置: {setting[0]}')
    
    print('✅ 默认设置插入完成')
else:
    print('\n⚠️  bot_settings 表已存在')

# 更新 Alembic 版本
print('\n📋 更新 Alembic 版本...')
cur.execute("UPDATE alembic_version SET version_num = '20251009_add_bot_settings_user_sessions'")

conn.commit()
conn.close()

print('\n✅ 所有表创建完成！')
print('Alembic 版本已更新为: 20251009_add_bot_settings_user_sessions')

