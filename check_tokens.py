import sqlite3
import os

db_path = os.path.join('data', 'bot_memory.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT id, nom, token_wa, whatsapp_phone_id FROM businesses')
rows = cursor.fetchall()
for r in rows:
    print(f"{r['nom']} (ID: {r['id']}): PhoneID={r['whatsapp_phone_id']}, Token={r['token_wa'][:10]}...")

conn.close()
