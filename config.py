"""
Configuration centrale de l'application.

Charge les variables d'environnement depuis le fichier .env
et expose des classes de configuration par environnement.
"""

import os
from dotenv import load_dotenv

# Charger le fichier .env situé à la racine du projet
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))


class Config:
    """Configuration de base — valeurs partagées par tous les environnements."""

    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    GROQ_API_KEY: str = os.getenv('GROQ_API_KEY', '')
    VERIFY_TOKEN: str = os.getenv('VERIFY_TOKEN', '')
    MASTER_PASSWORD_HASH: str = os.getenv('MASTER_PASSWORD_HASH', '')
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'change-me')
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'fallback-jwt-secret-key-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = 604800  # 7 jours en secondes
    DB_PATH: str = 'data/bot_memory.db'


class DevelopmentConfig(Config):
    """Configuration pour le développement local."""

    DEBUG: bool = True


class ProductionConfig(Config):
    """Configuration pour la production."""

    DEBUG: bool = False


config: dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
