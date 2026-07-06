import sqlite3
import random
import os
import shutil
from pathlib import Path

BASE_DIR = Path(r"c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro")
DB_PATH = BASE_DIR / "data" / "bot_memory.db"
BACKUP_PATH = BASE_DIR / "data" / "bot_memory_backup.db"
UPLOADS_DIR = BASE_DIR / "app" / "static" / "uploads" / "businesses"

def migrate():
    # 1. Sauvegarde
    print(f"Création de la sauvegarde : {BACKUP_PATH}")
    shutil.copy2(DB_PATH, BACKUP_PATH)
    
    # 2. Désactivation des Foreign Keys pour autoriser l'update manuel si besoin
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF;")
    cursor = conn.cursor()
    
    # Trouver tous les biz_ids qui contiennent "_" (les slugs email)
    cursor.execute("SELECT id FROM businesses WHERE id LIKE '%_%'")
    old_businesses = cursor.fetchall()
    
    if not old_businesses:
        print("Aucun compte avec l'ancien format d'ID trouvé.")
        conn.close()
        return
        
    print(f"{len(old_businesses)} comptes trouvés pour la migration.")
    
    for row in old_businesses:
        old_id = row[0]
        
        # Générer le nouvel ID unique
        while True:
            new_id = str(random.randint(10000000, 99999999))
            cursor.execute("SELECT id FROM businesses WHERE id = ?", (new_id,))
            if not cursor.fetchone():
                break
                
        print(f"Migration de {old_id} vers {new_id}...")
        
        # Mettre à jour l'ID principal
        # En même temps, mettre à jour le logo vitrine URL
        cursor.execute("""
            UPDATE businesses 
            SET id = ?, vitrine_logo_url = REPLACE(vitrine_logo_url, ?, ?) 
            WHERE id = ?
        """, (new_id, f"/{old_id}/", f"/{new_id}/", old_id))
        
        # Mettre à jour les tables avec foreign key ou références simples
        tables_to_update = [
            "history", "reservations", "clients", "client_tags", 
            "employees", "campaign_queue", "ai_agents", "tags", 
            "notifications_master"
        ]
        for table in tables_to_update:
            cursor.execute(f"UPDATE {table} SET business_id = ? WHERE business_id = ?", (new_id, old_id))
            
        # Table products (avec remplacement d'URL)
        cursor.execute("""
            UPDATE products 
            SET business_id = ?, image_url = REPLACE(image_url, ?, ?) 
            WHERE business_id = ?
        """, (new_id, f"/{old_id}/", f"/{new_id}/", old_id))
        
        # Renommer le dossier physique s'il existe
        old_dir = UPLOADS_DIR / old_id
        new_dir = UPLOADS_DIR / new_id
        if old_dir.exists() and old_dir.is_dir():
            print(f"Renommage du dossier d'uploads de {old_id} vers {new_id}")
            old_dir.rename(new_dir)
            
    conn.commit()
    conn.close()
    print("Migration terminée avec succès !")

if __name__ == "__main__":
    migrate()
