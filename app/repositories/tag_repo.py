import sqlite3
from typing import List, Dict, Any, Optional

from app.models.schema import get_db_path

def get_business_tags(business_id: str) -> List[sqlite3.Row]:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM tags WHERE business_id = ? ORDER BY created_at DESC",
        (business_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def create_tag(business_id: str, name: str, tag_type: str, color: str, description: str) -> int:
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tags (business_id, type, name, color, description) VALUES (?, ?, ?, ?, ?)",
        (business_id, tag_type, name, color, description)
    )
    tag_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tag_id

def update_tag(tag_id: int, business_id: str, name: str, tag_type: str, color: str, description: str) -> bool:
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tags SET name = ?, type = ?, color = ?, description = ? WHERE id = ? AND business_id = ?",
        (name, tag_type, color, description, tag_id, business_id)
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def delete_tag(tag_id: int, business_id: str) -> bool:
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tags WHERE id = ? AND business_id = ?", (tag_id, business_id))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def add_tag_to_order(order_id: int, tag_id: int):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO order_tags (order_id, tag_id) VALUES (?, ?)", (order_id, tag_id))
    conn.commit()
    conn.close()

def add_tag_to_client(wa_id: str, business_id: str, tag_id: int):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO client_tags (wa_id, business_id, tag_id) VALUES (?, ?, ?)", (wa_id, business_id, tag_id))
    conn.commit()
    conn.close()

def get_tags_for_order(order_id: int) -> List[sqlite3.Row]:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT t.* FROM tags t 
           JOIN order_tags ot ON t.id = ot.tag_id 
           WHERE ot.order_id = ?''',
        (order_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_tags_for_client(wa_id: str, business_id: str) -> List[sqlite3.Row]:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT t.* FROM tags t 
           JOIN client_tags ct ON t.id = ct.tag_id 
           WHERE ct.wa_id = ? AND ct.business_id = ?''',
        (wa_id, business_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_tag_by_name(business_id: str, name: str) -> Optional[sqlite3.Row]:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM tags WHERE business_id = ? AND LOWER(name) = LOWER(?) LIMIT 1",
        (business_id, name)
    )
    row = cursor.fetchone()
    conn.close()
    return row
