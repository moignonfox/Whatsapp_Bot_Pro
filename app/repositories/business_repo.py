"""
business_repo.py — Accès aux données des entreprises (businesses).

Fournit les fonctions CRUD pour la table 'businesses'.
"""

import sqlite3
from typing import List, Optional

from app.models.schema import get_db_path


def add_or_update(
    biz_id: str,
    nom: str,
    phone_id: str,
    token: str,
    password: str,
    prompt: str,
    msg_confirm: str,
    msg_cancel: str,
    msg_ready: str,
    business_type: str = 'restaurant',
    plan_abonnement: str = 'BASIC',
    is_active: int = 1,
    owner_phone: str = None,
    drip_j3_enabled: int = 0,
    drip_j3_msg: str = None,
    debounce_delay: int = 3,
    buffer_minutes: int = 0
) -> None:
    """Ajoute ou met à jour un business dans la base."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Vérifier si le business existe déjà
    cursor.execute("SELECT id FROM businesses WHERE id = ?", (biz_id,))
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute(
            """UPDATE businesses SET 
               nom = ?, whatsapp_phone_id = ?, token_wa = ?, password = ?,
               prompt = ?, msg_confirm = ?, msg_cancel = ?, msg_ready = ?, 
               business_type = ?, plan_abonnement = ?, is_active = ?, 
               owner_phone = ?, drip_j3_enabled = ?, drip_j3_msg = ?, debounce_delay = ?, buffer_minutes = ?, email = ?
               WHERE id = ?""",
            (nom, phone_id, token, password, prompt, msg_confirm, msg_cancel, msg_ready, business_type, 
             plan_abonnement, is_active, owner_phone, drip_j3_enabled, drip_j3_msg, debounce_delay, buffer_minutes, None, biz_id)
        )
    else:
        cursor.execute(
            """INSERT INTO businesses
               (id, nom, whatsapp_phone_id, token_wa, password,
                prompt, msg_confirm, msg_cancel, msg_ready, business_type, plan_abonnement, is_active, owner_phone, 
                drip_j3_enabled, drip_j3_msg, debounce_delay, buffer_minutes, email)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (biz_id, nom, phone_id, token, password, prompt, msg_confirm, msg_cancel, msg_ready, business_type, 
             plan_abonnement, is_active, owner_phone, drip_j3_enabled, drip_j3_msg, debounce_delay, buffer_minutes, None),
        )
        
    conn.commit()
        
    conn.commit()
    conn.close()

def create_business_registration(
    biz_id: str,
    email: str,
    password: str,
    nom: str,
    owner_name: str,
    owner_phone: str,
    requested_bot_phone: str,
    business_type: str,
    devise: str
) -> None:
    """Création d'un nouveau compte en attente de validation via l'application mobile."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute(
        """INSERT INTO businesses
           (id, email, password, nom, owner_name, owner_phone, requested_bot_phone, business_type, devise, is_approved, is_active, plan_abonnement, prompt, msg_confirm, msg_cancel, msg_ready)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, 'BASIC', '', '', '', '')""",
        (biz_id, email, password, nom, owner_name, owner_phone, requested_bot_phone, business_type, devise),
    )
    
    conn.commit()
    conn.close()

def update_basic_profile(biz_id: str, nom: str = None, is_active: int = None, prompt: str = None, msg_confirm: str = None, horaires_json: str = None, email: str = None, owner_phone: str = None) -> None:
    """Met à jour les paramètres de base du profil via l'application mobile."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Construire la requête dynamiquement
    fields = []
    values = []
    
    if nom is not None:
        fields.append("nom = ?")
        values.append(nom)
    if is_active is not None:
        fields.append("is_active = ?")
        values.append(is_active)
    if prompt is not None:
        fields.append("prompt = ?")
        values.append(prompt)
    if msg_confirm is not None:
        fields.append("msg_confirm = ?")
        values.append(msg_confirm)
    if horaires_json is not None:
        fields.append("horaires_json = ?")
        values.append(horaires_json)
    if email is not None:
        fields.append("email = ?")
        values.append(email)
    if owner_phone is not None:
        fields.append("owner_phone = ?")
        values.append(owner_phone)
        
    if fields:
        query = "UPDATE businesses SET " + ", ".join(fields) + " WHERE id = ?"
        values.append(biz_id)
        cursor.execute(query, tuple(values))
        conn.commit()
        
    conn.close()
def set_business_horaires(biz_id: str, horaires_json: str) -> None:
    """Met à jour les horaires d'ouverture de l'entreprise."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE businesses SET horaires_json = ? WHERE id = ?",
        (horaires_json, biz_id)
    )
    conn.commit()
    conn.close()

def set_requested_bot_phone(biz_id: str, phone: str) -> None:
    """Met à jour le numéro de téléphone demandé pour le bot."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE businesses SET requested_bot_phone = ? WHERE id = ?",
        (phone, biz_id)
    )
    conn.commit()
    conn.close()

def set_fcm_token(biz_id: str, fcm_token: str) -> None:
    """Met à jour le token Firebase Cloud Messaging (FCM) du business."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE businesses SET fcm_token = ? WHERE id = ?",
        (fcm_token, biz_id)
    )
    conn.commit()
    conn.close()



def set_vitrine_settings(biz_id: str, color: str, logo_url: str = None) -> None:
    """Met à jour les paramètres de la vitrine d'un business."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    if logo_url is not None:
        cursor.execute(
            "UPDATE businesses SET vitrine_color = ?, vitrine_logo_url = ? WHERE id = ?",
            (color, logo_url, biz_id)
        )
    else:
        cursor.execute(
            "UPDATE businesses SET vitrine_color = ? WHERE id = ?",
            (color, biz_id)
        )
    conn.commit()
    conn.close()


def get_by_phone_id(phone_id: str) -> Optional[sqlite3.Row]:
    """Recherche un business par son WhatsApp Phone Number ID."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM businesses WHERE whatsapp_phone_id = ?",
        (phone_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def get_by_id(biz_id: str) -> Optional[sqlite3.Row]:
    """Recherche un business par son identifiant unique."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM businesses WHERE id = ?",
        (biz_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row

def get_by_email(email: str) -> Optional[sqlite3.Row]:
    """Recherche un business par son adresse email."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM businesses WHERE LOWER(email) = LOWER(?)",
        (email,),
    )
    row = cursor.fetchone()
    conn.close()
    return row

def get_all_businesses() -> List[sqlite3.Row]:
    """Retourne la liste de tous les business inscrits."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM businesses ORDER BY nom ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_business(biz_id: str) -> None:
    """Supprime definitivement un business de la base."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM businesses WHERE id = ?", (biz_id,))
    conn.commit()
    conn.close()


def toggle_active(biz_id: str, is_active: int) -> None:
    """Active ou desactive un business."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("UPDATE businesses SET is_active = ? WHERE id = ?", (is_active, biz_id))
    conn.commit()
    conn.close()


def update_owner_phone(biz_id: str, owner_phone: str) -> None:
    """Met à jour le numéro de téléphone personnel du gérant."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("UPDATE businesses SET owner_phone = ? WHERE id = ?", (owner_phone, biz_id))
    conn.commit()
    conn.close()

def update_bot_phone(biz_id: str, bot_phone: str) -> None:
    """Met à jour le numéro WhatsApp du bot pour la vitrine."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("UPDATE businesses SET requested_bot_phone = ? WHERE id = ?", (bot_phone, biz_id))
    conn.commit()
    conn.close()


def get_human_mode(biz_id: str) -> dict:
    """Retourne le dictionnaire des conversations en mode humain pour un business."""
    import json
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT human_mode FROM businesses WHERE id = ?", (biz_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def set_human_mode(biz_id: str, wa_id: str, active: bool) -> None:
    """Active ou desactive le mode humain pour une conversation specifique."""
    import json
    from datetime import datetime, timezone
    modes = get_human_mode(biz_id)
    if active:
        modes[wa_id] = datetime.now(timezone.utc).isoformat()
    else:
        modes.pop(wa_id, None)
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE businesses SET human_mode = ? WHERE id = ?",
        (json.dumps(modes), biz_id),
    )
    conn.commit()
    conn.close()


def is_human_mode(biz_id: str, wa_id: str) -> bool:
    """Verifie si une conversation est en mode humain."""
    modes = get_human_mode(biz_id)
    return wa_id in modes


def update_routing_mode(biz_id: str, routing_mode: str) -> None:
    """Met à jour le mode de routage des agents IA pour un business.
    
    Valeurs acceptées : 'visible' | 'invisible'
    """
    allowed = {'visible', 'invisible'}
    if routing_mode not in allowed:
        raise ValueError(f"Mode de routage invalide : {routing_mode!r}")
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE businesses SET agent_routing_mode = ? WHERE id = ?",
        (routing_mode, biz_id),
    )
    conn.commit()
    conn.close()
