"""
check_models.py — Liste les modèles Gemini disponibles.

Usage : python scripts/check_models.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config as app_config

from google import genai

cfg = app_config['default']
client = genai.Client(api_key=cfg.GEMINI_API_KEY)

print("--- Liste des modèles disponibles ---")
try:
    for model in client.models.list():
        print(f"Nom du modèle : {model.name}")
except Exception as e:
    print(f"Erreur lors de la liste : {e}")
