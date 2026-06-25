import sqlite3
import os
import sys

# Ajouter le chemin du projet pour pouvoir importer depuis app.models.schema
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash
from app.models.schema import get_db_path

def migrate():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"La base de données n'existe pas à l'emplacement : {db_path}")
        return

    print("Connexion à la base de données...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Récupérer tous les businesses
    cursor.execute("SELECT id, nom, password FROM businesses")
    businesses = cursor.fetchall()

    if not businesses:
        print("Aucun business trouvé.")
        conn.close()
        return

    print(f"{len(businesses)} business(es) trouvé(s). Début de la migration...")

    updated_count = 0
    for biz_id, nom, password in businesses:
        # Si le mot de passe est déjà un hash de werkzeug (ils commencent généralement par scrypt: ou pbkdf2: ou sont très longs), on l'ignore.
        if password and not (password.startswith('scrypt:') or password.startswith('pbkdf2:')):
            hashed = generate_password_hash(password)
            cursor.execute("UPDATE businesses SET password = ? WHERE id = ?", (hashed, biz_id))
            updated_count += 1
            print(f" ✓ Mot de passe haché pour {nom} ({biz_id})")
        elif not password:
            print(f" ⚠️ Le mot de passe pour {nom} ({biz_id}) est vide, ignoré.")
        else:
            print(f" ℹ️ Le mot de passe pour {nom} ({biz_id}) semble déjà haché.")

    conn.commit()
    conn.close()
    print(f"\nMigration terminée. {updated_count} mot(s) de passe mis à jour.")

if __name__ == '__main__':
    migrate()
