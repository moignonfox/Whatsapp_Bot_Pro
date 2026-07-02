"""Service CRM — Extraction et sauvegarde de l'identité client."""
from app.repositories import client_repo


def extract_and_save_client_name(reply, wa_id, biz_id):
    """Cherche un tag [CLIENT: Nom] dans la réponse IA, met à jour le CRM.
    
    Retourne la réponse nettoyée (sans le tag).
    """
    if "[CLIENT:" not in reply:
        return reply
    
    try:
        start = reply.find("[CLIENT:") + len("[CLIENT:")
        end = reply.find("]", start)
        nouveau_nom = reply[start:end].strip()
        
        # Mise à jour via le repository CRM
        client_repo.update_name(biz_id, wa_id, nouveau_nom)
    except Exception as e:
        print(f"Erreur capture nom : {e}")
    
    # On nettoie la réponse avec regex pour être robuste
    import re
    reply = re.sub(r'\[CLIENT:.*?\]', '', reply).strip()
    
    return reply
