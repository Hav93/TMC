import sqlite3
import json

conn = sqlite3.connect('data/bot.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT id, file_name, message_id, file_unique_id, file_access_hash, media_json, status 
    FROM download_tasks 
    ORDER BY id DESC 
    LIMIT 3
''')

rows = cursor.fetchall()

print("=" * 80)
print("Latest 3 Tasks")
print("=" * 80)

for row in rows:
    task_id, file_name, msg_id, unique_id, access_hash, media_json, status = row
    print(f"\n[Task {task_id}] {file_name}")
    print(f"  Message ID: {msg_id}")
    print(f"  Unique ID: {unique_id}")
    print(f"  Access Hash: {access_hash}")
    print(f"  Status: {status}")
    if media_json:
        media = json.loads(media_json)
        print(f"  Media JSON: {json.dumps(media, indent=4, ensure_ascii=False)}")
    else:
        print(f"  Media JSON: None")

conn.close()
print("\n" + "=" * 80)

