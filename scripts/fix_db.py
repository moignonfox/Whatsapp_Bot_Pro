"""
fix_db.py — Initialise la base de données et applique les migrations.

Usage : python scripts/fix_db.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.schema import init_db, update_schema

if __name__ == "__main__":
    init_db()
    update_schema()
    print("\n🚀 Base de données 100% prête !")
