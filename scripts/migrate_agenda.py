import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'bot_memory.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Add buffer_minutes to businesses
    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN buffer_minutes INTEGER DEFAULT 0")
        print("Added buffer_minutes to businesses.")
    except sqlite3.OperationalError:
        print("buffer_minutes already exists in businesses.")

    # 2. Add duree_minutes to products
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN duree_minutes INTEGER DEFAULT 30")
        print("Added duree_minutes to products.")
    except sqlite3.OperationalError:
        print("duree_minutes already exists in products.")

    # 3. Add horaires_json to employees
    try:
        # Default to a generic schedule for existing employees
        default_schedule = '{"lun":["09:00","18:00"],"mar":["09:00","18:00"],"mer":["09:00","18:00"],"jeu":["09:00","18:00"],"ven":["09:00","18:00"],"sam":["09:00","14:00"],"dim":[]}'
        cursor.execute(f"ALTER TABLE employees ADD COLUMN horaires_json TEXT DEFAULT '{default_schedule}'")
        print("Added horaires_json to employees.")
    except sqlite3.OperationalError:
        print("horaires_json already exists in employees.")

    # 4. Add fields to reservations
    cols_to_add = [
        ("date_heure_debut", "DATETIME"),
        ("employee_id", "INTEGER"),
        ("product_id", "INTEGER"),
        ("rappel_envoye", "INTEGER DEFAULT 0")
    ]
    for col_name, col_type in cols_to_add:
        try:
            cursor.execute(f"ALTER TABLE reservations ADD COLUMN {col_name} {col_type}")
            print(f"Added {col_name} to reservations.")
        except sqlite3.OperationalError:
            print(f"{col_name} already exists in reservations.")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == '__main__':
    migrate()
