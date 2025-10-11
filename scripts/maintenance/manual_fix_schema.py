#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动修复数据库Schema
"""

import sys
sys.path.insert(0, 'app/backend')

from database import get_db
from sqlalchemy import text
import asyncio


async def run_migration():
    """执行数据库Schema修复"""
    async for db in get_db():
        print("=" * 60)
        print("🔧 手动修复数据库Schema")
        print("=" * 60)
        
        # ========== 修复 keywords 表 ==========
        print("\n📋 检查 keywords 表...")
        result = await db.execute(text('PRAGMA table_info(keywords)'))
        cols = {row[1] for row in result.fetchall()}
        print(f"当前列: {cols}")
        
        if 'is_regex' not in cols:
            print("  ➕ 添加 is_regex...")
            await db.execute(text('ALTER TABLE keywords ADD COLUMN is_regex BOOLEAN DEFAULT 0'))
        else:
            print("  ✅ is_regex 已存在")
        
        if 'case_sensitive' not in cols:
            print("  ➕ 添加 case_sensitive...")
            await db.execute(text('ALTER TABLE keywords ADD COLUMN case_sensitive BOOLEAN DEFAULT 0'))
        else:
            print("  ✅ case_sensitive 已存在")
        
        await db.commit()
        print("✅ keywords 表修复完成")
        
        # ========== 修复 replace_rules 表 ==========
        print("\n📋 检查 replace_rules 表...")
        result = await db.execute(text('PRAGMA table_info(replace_rules)'))
        cols = {row[1] for row in result.fetchall()}
        print(f"当前列: {cols}")
        
        if 'name' not in cols:
            print("  ➕ 添加 name...")
            await db.execute(text('ALTER TABLE replace_rules ADD COLUMN name VARCHAR(100)'))
            # 为现有记录设置默认名称
            result = await db.execute(text('SELECT COUNT(*) FROM replace_rules'))
            count = result.scalar()
            if count > 0:
                await db.execute(text("UPDATE replace_rules SET name = '替换规则 #' || id WHERE name IS NULL"))
        else:
            print("  ✅ name 已存在")
        
        if 'priority' not in cols:
            print("  ➕ 添加 priority...")
            await db.execute(text('ALTER TABLE replace_rules ADD COLUMN priority INTEGER DEFAULT 0'))
        else:
            print("  ✅ priority 已存在")
        
        if 'is_regex' not in cols:
            print("  ➕ 添加 is_regex...")
            await db.execute(text('ALTER TABLE replace_rules ADD COLUMN is_regex BOOLEAN DEFAULT 1'))
        else:
            print("  ✅ is_regex 已存在")
        
        if 'is_global' not in cols:
            print("  ➕ 添加 is_global...")
            await db.execute(text('ALTER TABLE replace_rules ADD COLUMN is_global BOOLEAN DEFAULT 0'))
        else:
            print("  ✅ is_global 已存在")
        
        await db.commit()
        print("✅ replace_rules 表修复完成")
        
        # ========== 修复 message_logs 表 ==========
        print("\n📋 检查 message_logs 表...")
        result = await db.execute(text('PRAGMA table_info(message_logs)'))
        cols = {row[1] for row in result.fetchall()}
        print(f"当前列: {cols}")
        
        if 'rule_id' not in cols:
            print("  ➕ 添加 rule_id...")
            await db.execute(text('ALTER TABLE message_logs ADD COLUMN rule_id INTEGER'))
        else:
            print("  ✅ rule_id 已存在")
        
        if 'source_message_id' not in cols:
            print("  ➕ 添加 source_message_id...")
            await db.execute(text('ALTER TABLE message_logs ADD COLUMN source_message_id INTEGER'))
        else:
            print("  ✅ source_message_id 已存在")
        
        if 'target_message_id' not in cols:
            print("  ➕ 添加 target_message_id...")
            await db.execute(text('ALTER TABLE message_logs ADD COLUMN target_message_id INTEGER'))
        else:
            print("  ✅ target_message_id 已存在")
        
        if 'original_text' not in cols:
            print("  ➕ 添加 original_text...")
            await db.execute(text('ALTER TABLE message_logs ADD COLUMN original_text TEXT'))
        else:
            print("  ✅ original_text 已存在")
        
        if 'processed_text' not in cols:
            print("  ➕ 添加 processed_text...")
            await db.execute(text('ALTER TABLE message_logs ADD COLUMN processed_text TEXT'))
        else:
            print("  ✅ processed_text 已存在")
        
        await db.commit()
        print("✅ message_logs 表修复完成")
        
        print("\n" + "=" * 60)
        print("🎉 所有表Schema修复完成！")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_migration())

