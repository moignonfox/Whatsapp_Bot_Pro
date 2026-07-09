import re

def format_whatsapp_number(number: str) -> str:
    """Nettoie le numéro pour ne garder que les chiffres et supprime les + ou 00."""
    if not number:
        return ""
    cleaned = re.sub(r'\D', '', number)
    if cleaned.startswith('00'):
        cleaned = cleaned[2:]
    return cleaned

def validate_whatsapp_number(cleaned: str) -> tuple[bool, str]:
    """
    Vérifie si le numéro nettoyé semble être au format international.
    Retourne (est_valide, message_erreur).
    """
    if not cleaned:
        return False, "Numéro invalide"
    if cleaned.startswith('0'):
        return False, "Veuillez inclure l'indicatif du pays (ex: 225... au lieu de 0...)"
    if len(cleaned) < 10:
        return False, "Le numéro semble trop court. N'oubliez pas l'indicatif du pays."
    return True, ""
