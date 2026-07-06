import sqlite3
import os

db_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\database.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE notifications_master ADD COLUMN title TEXT')
    print("SUCCESS: Column 'title' added to 'notifications_master'.")
except sqlite3.OperationalError as e:
    print(f"ERROR or ALREADY EXISTS: {e}")

conn.commit()
conn.close()
