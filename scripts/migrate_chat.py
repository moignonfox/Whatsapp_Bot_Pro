"""
migrate_chat.py -- Applique les migrations de schema pour le chat inbox.

Usage: python scripts/migrate_chat.py
"""

import sys
import os

# Ajouter la racine du projet au sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.schema import get_db_path, update_schema

if __name__ == '__main__':
    print(f"[migrate_chat] Base de donnees : {get_db_path()}")
    update_schema()
    print("[migrate_chat] Migration terminee avec succes.")
