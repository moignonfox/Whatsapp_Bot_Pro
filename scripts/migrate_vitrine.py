import sqlite3

db_path = r'c:\Users\moign\OneDrive\Whatsapp_Bot_Pro\data\bot_memory.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute('ALTER TABLE products ADD COLUMN image_url TEXT')
except sqlite3.OperationalError:
    pass

try:
    c.execute('ALTER TABLE products ADD COLUMN is_visible INTEGER DEFAULT 1')
except sqlite3.OperationalError:
    pass

try:
    c.execute('ALTER TABLE businesses ADD COLUMN vitrine_color TEXT DEFAULT "#5b6af0"')
except sqlite3.OperationalError:
    pass

try:
    c.execute('ALTER TABLE businesses ADD COLUMN vitrine_logo_url TEXT')
except sqlite3.OperationalError:
    pass

conn.commit()
conn.close()
print('Schema updated successfully')
