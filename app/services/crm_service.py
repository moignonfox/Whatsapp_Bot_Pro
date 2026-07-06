"""Service CRM — Extraction et sauvegarde de l'identité client."""
from app.repositories import client_repo


import re

def extract_and_save_client_info(reply, wa_id, biz_id):
    """Cherche les tags [CLIENT:], [DISPLAY_NAME:], et [NOM_CORRECTION:] dans la réponse IA, 
    et met à jour le CRM. Retourne la réponse nettoyée (sans les tags).
    """
    if "[" not in reply:
        return reply

    try:
        # 1. Extraction du nom initial complet [CLIENT: Nom]
        client_match = re.search(r'\[CLIENT:\s*(.*?)\]', reply)
        if client_match:
            nouveau_nom = client_match.group(1).strip()
            client_repo.update_name(biz_id, wa_id, nouveau_nom)

        # 2. Changement du nom d'usage [DISPLAY_NAME: Nom]
        display_match = re.search(r'\[DISPLAY_NAME:\s*(.*?)\]', reply)
        if display_match:
            nouveau_display = display_match.group(1).strip()
            client_repo.set_display_name(biz_id, wa_id, nouveau_display)

        # 3. Correction explicite du vrai nom [NOM_CORRECTION: Nom]
        correction_match = re.search(r'\[NOM_CORRECTION:\s*(.*?)\]', reply)
        if correction_match:
            vrai_nom = correction_match.group(1).strip()
            client_repo.correct_real_name(biz_id, wa_id, vrai_nom)

    except Exception as e:
        print(f"Erreur capture nom/display_name : {e}")

    # On nettoie la réponse avec regex pour retirer tous ces tags
    reply = re.sub(r'\[CLIENT:.*?\]', '', reply)
    reply = re.sub(r'\[DISPLAY_NAME:.*?\]', '', reply)
    reply = re.sub(r'\[NOM_CORRECTION:.*?\]', '', reply)
    
    return reply.strip()
