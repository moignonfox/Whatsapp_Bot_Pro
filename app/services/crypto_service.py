"""
crypto_service.py — Chiffrement/Déchiffrement symétrique des données sensibles.

Utilise Fernet (AES-128-CBC + HMAC-SHA256) pour protéger les tokens
WhatsApp, clés CinetPay et autres données sensibles stockées en base.

La clé ENCRYPTION_KEY doit être définie dans le fichier .env.
"""

import os
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Chargée une seule fois au démarrage du module
_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Retourne l'instance Fernet initialisée (singleton)."""
    global _fernet
    if _fernet is None:
        key = os.environ.get('ENCRYPTION_KEY', '')
        if not key:
            raise RuntimeError(
                "ENCRYPTION_KEY manquante dans le .env. "
                "Générez une clé avec : python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        _fernet = Fernet(key.encode())
    return _fernet


def encrypt_token(plain_text: str) -> str:
    """Chiffre une chaîne sensible et retourne la version chiffrée (str).

    Retourne la valeur originale si elle est vide ou None.
    """
    if not plain_text:
        return plain_text or ''
    try:
        fernet = _get_fernet()
        return fernet.encrypt(plain_text.encode()).decode()
    except Exception as e:
        logger.error("Erreur de chiffrement : %s", e, exc_info=True)
        raise


def decrypt_token(cipher_text: str) -> str:
    """Déchiffre une chaîne chiffrée par Fernet et retourne le texte clair.

    - Retourne une chaîne vide si cipher_text est vide ou None.
    - Retourne la valeur originale si elle n'est pas chiffrée
      (rétrocompatibilité pendant la migration).
    """
    if not cipher_text:
        return ''
    try:
        fernet = _get_fernet()
        return fernet.decrypt(cipher_text.encode()).decode()
    except InvalidToken:
        # Le token n'est pas chiffré (données legacy, migration en cours)
        logger.warning(
            "decrypt_token : valeur non chiffrée détectée — lecture en clair (migration requise)."
        )
        return cipher_text
    except Exception as e:
        logger.error("Erreur de déchiffrement : %s", e, exc_info=True)
        raise


def is_encrypted(value: str) -> bool:
    """Indique si une valeur est déjà chiffrée par Fernet.

    Utile pour le script de migration afin d'éviter le double-chiffrement.
    """
    if not value:
        return False
    try:
        fernet = _get_fernet()
        fernet.decrypt(value.encode())
        return True
    except InvalidToken:
        return False
    except Exception:
        return False
