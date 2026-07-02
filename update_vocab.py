import sqlite3
import json

db_path = 'data/bot_memory.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Vocabulary for services and reservations (restaurants, salon, etc.)
service_vocab = {
    'status_ready': 'Client arrivé',
    'btn_ready': 'Client arrivé',
    'order_name': 'réservation',
    'catalog_name': 'Services'
}

restaurant_vocab = {
    'status_ready': 'Client arrivé',
    'btn_ready': 'Client arrivé',
    'order_name': 'réservation',
    'catalog_name': 'Menu'
}

cursor.execute("UPDATE sectors SET vocab = ? WHERE id = 'service'", (json.dumps(service_vocab, ensure_ascii=False),))
cursor.execute("UPDATE sectors SET vocab = ? WHERE id = 'restaurant'", (json.dumps(restaurant_vocab, ensure_ascii=False),))

conn.commit()
conn.close()
print('Vocab updated.')
