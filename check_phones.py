import sqlite3
import os

db_path = os.path.join('data', 'bot_memory.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT id, nom, owner_phone FROM businesses')
rows = cursor.fetchall()
for r in rows:
    owner_phone = r['owner_phone']
    if not owner_phone:
        continue
    
    clean_phone = ''.join(c for c in owner_phone if c.isdigit())
    if clean_phone.startswith('00'):
        clean_phone = clean_phone[2:]
    if len(clean_phone) == 8:
        clean_phone = f'228{clean_phone}'
        
    print(f"{r['nom']} (ID: {r['id']}): Raw='{owner_phone}' -> Clean='{clean_phone}'")

conn.close()
