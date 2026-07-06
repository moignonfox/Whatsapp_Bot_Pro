import sqlite3
import os

db_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\data\bot_memory.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS notifications_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    title TEXT,
    message TEXT NOT NULL,
    business_id TEXT,
    is_read BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()
print("SUCCESS: Table 'notifications_master' created in bot_memory.db.")

try:
    cursor.execute('ALTER TABLE notifications_master ADD COLUMN title TEXT')
    print("SUCCESS: Added title column if missing.")
except Exception as e:
    pass

conn.commit()
conn.close()
