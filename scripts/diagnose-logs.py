#!/usr/bin/env python3
"""
转发日志诊断工具
快速检查数据库中是否有日志记录，以及表结构是否正确
"""
import sqlite3
import sys
from pathlib import Path

# 数据库文件路径
DB_PATH = Path("/app/data/bot.db")

def main():
    print("=" * 70)
    print("转发日志诊断工具")
    print("=" * 70)
    
    if not DB_PATH.exists():
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        sys.exit(1)
    
    print(f"📂 数据库路径: {DB_PATH}\n")
    
    # 连接数据库
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # 1. 检查表是否存在
        print("🔍 检查 message_logs 表...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='message_logs'")
        if not cursor.fetchone():
            print("❌ message_logs 表不存在！")
            return
        print("✅ message_logs 表存在\n")
        
        # 2. 检查表结构
        print("🔍 检查表结构...")
        cursor.execute("PRAGMA table_info(message_logs)")
        columns = cursor.fetchall()
        
        required_columns = [
            'source_message_id',
            'target_message_id',
            'media_type',
            'content_hash',
            'media_hash',
            'sender_id',
            'sender_username',
            'status',
            'error_message',
            'processing_time'
        ]
        
        column_names = [col[1] for col in columns]
        print(f"表中现有字段 ({len(column_names)}):")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        print(f"\n检查必需字段:")
        missing_columns = []
        for req_col in required_columns:
            if req_col in column_names:
                print(f"  ✅ {req_col}")
            else:
                print(f"  ❌ {req_col} - 缺失！")
                missing_columns.append(req_col)
        
        if missing_columns:
            print(f"\n⚠️  缺少 {len(missing_columns)} 个字段！")
            print("💡 需要运行数据库修复脚本:")
            print("   docker exec -it <container> python /app/scripts/fix-database-schema.py")
            print()
        else:
            print("\n✅ 所有必需字段都存在\n")
        
        # 3. 检查是否有日志记录
        print("🔍 检查日志记录...")
        cursor.execute("SELECT COUNT(*) FROM message_logs")
        total_count = cursor.fetchone()[0]
        print(f"总记录数: {total_count}")
        
        if total_count == 0:
            print("⚠️  数据库中没有任何日志记录！")
            print("💡 可能原因:")
            print("   1. 还没有进行过消息转发")
            print("   2. 转发时记录日志失败")
            print("   3. 表结构不正确导致插入失败\n")
        else:
            # 按状态统计
            cursor.execute("SELECT status, COUNT(*) FROM message_logs GROUP BY status")
            status_stats = cursor.fetchall()
            print(f"\n按状态统计:")
            for status, count in status_stats:
                print(f"  - {status or '(NULL)'}: {count}")
            
            # 最近的记录
            try:
                cursor.execute("""
                    SELECT id, source_chat_id, target_chat_id, status, created_at 
                    FROM message_logs 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """)
                recent_logs = cursor.fetchall()
                print(f"\n最近 {len(recent_logs)} 条记录:")
                for log in recent_logs:
                    print(f"  ID:{log[0]} | {log[1]} → {log[2]} | {log[3]} | {log[4]}")
            except sqlite3.OperationalError as e:
                print(f"\n⚠️  查询最近记录失败: {e}")
                print("这可能是因为表结构不完整")
        
        print("\n" + "=" * 70)
        if missing_columns:
            print("🔧 需要修复表结构")
        elif total_count == 0:
            print("⚠️  没有日志记录，请检查转发功能")
        else:
            print("✅ 数据库状态正常")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 诊断过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()

