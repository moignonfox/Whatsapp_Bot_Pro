"""
migrate_plans.py — Migration : ajout de la colonne plan_abonnement et de la table employees.

Exécuter UNE SEULE FOIS depuis la racine du projet :
    python scripts/migrate_plans.py
"""

import sys
import os

# Permet d'importer les modules du projet depuis le dossier scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.schema import update_schema

if __name__ == '__main__':
    print(">> Application des migrations de schema...")
    update_schema()
    print("[OK] Migration terminee !")
    print("   - Colonne 'plan_abonnement' ajoutee a la table 'businesses' (defaut : BASIC).")
    print("   - Table 'employees' creee (Multi-Employes -- offre PREMIUM).")

