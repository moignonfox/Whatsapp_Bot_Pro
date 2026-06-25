import sys
import os
import sqlite3
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.schema import get_db_path, update_schema

# We import the old constants to migrate them to the DB
from app.constants import LANGUAGES_MAPS

def migrate_sectors():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sectors (
            id               TEXT PRIMARY KEY,
            name             TEXT,
            vocab            TEXT
        )
    """)
    
    # Map the IDs to nice names for the Master Admin
    names = {
        'restaurant': '🍽️ Restaurant',
        'service': '🧹 Service / Intervention',
        'boutique': '🛍️ Boutique / E-commerce'
    }

    # Insert defaults
    for sect_id, vocab in LANGUAGES_MAPS.items():
        name = names.get(sect_id, sect_id)
        vocab_json = json.dumps(vocab, ensure_ascii=False)
        cursor.execute("""
            INSERT OR IGNORE INTO sectors (id, name, vocab)
            VALUES (?, ?, ?)
        """, (sect_id, name, vocab_json))
        
        # In case they were already there but we want to update the vocab
        cursor.execute("""
            UPDATE sectors SET vocab = ?, name = ? WHERE id = ?
        """, (vocab_json, name, sect_id))

    conn.commit()
    conn.close()
    
    print("Migration of sectors completed successfully.")

if __name__ == "__main__":
    migrate_sectors()
