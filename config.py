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
    ENCRYPTION_KEY: str = os.getenv('ENCRYPTION_KEY', '')

    # JWT : access token de courte durée (15 min), refresh indéfini (10 ans)
    JWT_ACCESS_TOKEN_EXPIRES: int = 900
    JWT_REFRESH_TOKEN_EXPIRES: int = 315360000

    # Activer la vérification de la blocklist JWT
    JWT_BLACKLIST_ENABLED: bool = True
    JWT_BLACKLIST_TOKEN_CHECKS: list = ['access', 'refresh']

    DB_PATH: str = 'data/bot_memory.db'
    META_APP_SECRET: str = os.getenv('META_APP_SECRET', '')


class DevelopmentConfig(Config):
    """Configuration pour le développement local."""

    DEBUG: bool = True


class ProductionConfig(Config):
    """Configuration pour la production."""

    DEBUG: bool = False

    @classmethod
    def validate(cls) -> None:
        """Vérifie que toutes les clés critiques sont définies en production."""
        missing = []
        if not cls.ENCRYPTION_KEY:
            missing.append('ENCRYPTION_KEY')
        if cls.JWT_SECRET_KEY == 'fallback-jwt-secret-key-change-me':
            missing.append('JWT_SECRET_KEY')
        if not cls.META_APP_SECRET:
            missing.append('META_APP_SECRET')
        if missing:
            raise RuntimeError(
                f"Variables d'environnement manquantes pour la production : {', '.join(missing)}"
            )


config: dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
