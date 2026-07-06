"""
migrate_encrypt_tokens.py -- Script one-shot de migration securisee.

Ce script chiffre tous les token_wa existants en clair dans la base de donnees
en utilisant Fernet (via crypto_service). A executer UNE SEULE FOIS apres
avoir defini ENCRYPTION_KEY dans le fichier .env.

Usage :
    .venv\\Scripts\\python.exe scripts\\migrate_encrypt_tokens.py
"""

import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

encryption_key = os.environ.get('ENCRYPTION_KEY', '')
if not encryption_key:
    print("[ERREUR] ENCRYPTION_KEY manquante dans le .env. Operation annulee.")
    sys.exit(1)

from app.services.crypto_service import encrypt_token, is_encrypted
from app.models.schema import get_db_path


def migrate():
    db_path = get_db_path()
    print(f"\nBase de donnees : {db_path}")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, nom, token_wa FROM businesses")
    rows = cursor.fetchall()

    total = len(rows)
    already_encrypted = 0
    empty_tokens = 0
    to_encrypt = []

    for row in rows:
        token = row['token_wa'] or ''
        if not token:
            empty_tokens += 1
        elif is_encrypted(token):
            already_encrypted += 1
        else:
            to_encrypt.append((row['id'], row['nom'], token))

    print(f"\nEtat actuel :")
    print(f"   Total businesses      : {total}")
    print(f"   Tokens vides          : {empty_tokens}")
    print(f"   Deja chiffres         : {already_encrypted}")
    print(f"   A chiffrer maintenant : {len(to_encrypt)}")

    if not to_encrypt:
        print("\n[OK] Tous les tokens sont deja chiffres. Aucune action requise.")
        conn.close()
        return

    print("\n[ATTENTION] Les business suivants auront leur token_wa chiffre :")
    for biz_id, nom, _ in to_encrypt:
        print(f"   - [{biz_id}] {nom}")

    print("\n" + "=" * 60)
    confirm = input("Tapez 'OUI' pour confirmer le chiffrement : ").strip()
    if confirm != 'OUI':
        print("[ANNULE] Operation annulee par l'utilisateur.")
        conn.close()
        return

    success = 0
    errors = 0
    for biz_id, nom, plain_token in to_encrypt:
        try:
            encrypted = encrypt_token(plain_token)
            cursor.execute(
                "UPDATE businesses SET token_wa = ? WHERE id = ?",
                (encrypted, biz_id)
            )
            print(f"   [OK] [{biz_id}] {nom} -- token chiffre.")
            success += 1
        except Exception as e:
            print(f"   [ERREUR] [{biz_id}] {nom} -- {e}")
            errors += 1

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print(f"Migration terminee : {success} token(s) chiffre(s), {errors} erreur(s).")
    if errors:
        print("[ATTENTION] Des erreurs sont survenues.")


if __name__ == '__main__':
    migrate()
