"""
setup_business.py — Enregistre un business de démonstration.

Usage : python scripts/setup_business.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.repositories.business_repo import add_or_update

if __name__ == "__main__":
    add_or_update(
        "fufu_togo",
        "La Résidence du Gourmet",
        "TON_PHONE_NUMBER_ID",
        "TON_ACCESS_TOKEN",
        "admin123",
        "", "", "", ""
    )
    print("✅ Business configuré avec succès !")
