#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data/bot.db')
cur = conn.cursor()
cur.execute("UPDATE alembic_version SET version_num = '20251009_fix_keywords_replace_schema'")
conn.commit()
conn.close()
print('Alembic版本已更新为: 20251009_fix_keywords_replace_schema')

