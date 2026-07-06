"""Service IA Hybride — Gemini (principal) avec fallback Groq."""
import logging
import requests
import json
import re
from datetime import datetime
from google import genai
from google.genai import types

from config import config as app_config
from app.repositories import conversation_repo, catalog_repo, order_repo

# ---------------------------------------------------------------------------
# Configuration et initialisation du client Gemini
# ---------------------------------------------------------------------------
cfg = app_config.get('default')
client = genai.Client(api_key=cfg.GEMINI_API_KEY)
logger = logging.getLogger(__name__)


# Table de résolution du ton (du plus restrictif au plus permissif)
_TONE_RANK = {'concis': 0, 'standard': 1, 'detaille': 2}


def _resolve_tone(biz_tone: str, agent_tone: str) -> str:
    """Retourne le ton le plus restrictif entre le business et l'agent.
    L'agent ne peut jamais être plus permissif que le business."""
    biz_rank = _TONE_RANK.get(biz_tone, 1)
    agent_rank = _TONE_RANK.get(agent_tone, 1)
    # On prend le minimum (= le plus restrictif)
    if agent_rank <= biz_rank:
        return agent_tone
    return biz_tone


def classify_intent(wa_id: str, business_id: str, user_message: str, agents: list,
                    last_agent_id: int = None) -> dict:
    """Route le message vers le bon agent IA via Groq (llama-3.1-8b-instant).

    Fallback : si le routeur échoue (JSON invalide OU timeout), retourne
    le dernier agent utilisé dans la session, ou le premier agent sinon.
    """
    if not agents:
        return None

    # --- Fallback par défaut : dernier agent ou premier de la liste ---
    fallback_agent = agents[0]
    if last_agent_id is not None:
        for a in agents:
            if a['id'] == last_agent_id:
                fallback_agent = a
                break

    groq_url = "https://api.groq.com/openai/v1/chat/completions"
    groq_headers = {
        "Authorization": f"Bearer {cfg.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    # Historique récent pour donner du contexte au routeur
    history = conversation_repo.get_recent_history(wa_id, business_id, limit=3)
    history_str = ""
    if history:
        history_str = "CONTEXTE RÉCENT DE LA CONVERSATION:\n"
        for msg in history:
            role = "Client" if msg['role'] == 'user' else "Assistant"
            history_str += f"{role}: {msg['content']}\n"

    # Description des agents avec leurs mots-clés
    agents_desc = []
    for a in agents:
        agents_desc.append(
            f"- ID: {a['id']} | Rôle: {a.get('role', 'Agent')} "
            f"| Mots-clés déclencheurs: [{a.get('intent_keywords', '')}]"
        )

    # Exemples few-shot pour ancrer le format JSON
    first_id = agents[0]['id']
    last_id = agents[-1]['id']
    few_shot = (
        "EXEMPLES DE ROUTAGE (format attendu) :\n"
        f"  Exemple 1 → {{\"agent_id\": {first_id}}}\n"
        f"  Exemple 2 → {{\"agent_id\": {last_id}}}\n"
        f"  Exemple 3 → {{\"agent_id\": {first_id}}}\n"
    )

    system_prompt = (
        "Tu es un routeur de messages. Ta SEULE tâche est de choisir l'agent "
        "dont les mots-clés correspondent le mieux au message du client.\n"
        "Tu DOIS répondre UNIQUEMENT par un objet JSON valide. Aucun texte avant ou après.\n\n"
        "AGENTS DISPONIBLES :\n"
        + "\n".join(agents_desc) + "\n\n"
        + few_shot +
        "\nRÈGLE : Si aucun mot-clé ne correspond, choisis l'agent le plus généraliste (ID le plus petit)."
    )

    full_user_content = f"{history_str}\nDERNIER MESSAGE DU CLIENT : {user_message}"

    groq_payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_user_content}
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 50,
    }

    try:
        # Timeout explicite de 3s pour ne pas bloquer la conversation
        resp = requests.post(groq_url, json=groq_payload, headers=groq_headers, timeout=3)
        data = resp.json()
        if "choices" in data:
            content = data["choices"][0]["message"]["content"].strip()
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*', '', content)
            parsed = json.loads(content)
            agent_id = int(parsed.get("agent_id", -1))
            for a in agents:
                if a['id'] == agent_id:
                    logger.info(
                        "[ROUTING] intent_detected=%s agent_id=%s agent_name=%s fallback=False",
                        user_message[:40], agent_id, a.get('name')
                    )
                    return a
    except Exception as e:
        logger.warning(
            "[ROUTING] Échec du routeur (%s) → fallback agent_id=%s",
            e, fallback_agent['id']
        )

    # Fallback : dernier agent utilisé ou premier de la liste
    logger.info(
        "[ROUTING] intent_detected=%s agent_id=%s agent_name=%s fallback=True",
        user_message[:40], fallback_agent['id'], fallback_agent.get('name')
    )
    return fallback_agent


def get_ai_response(wa_id: str, user_message: str, business_info: dict, agent_info: dict = None) -> str:
    """Génère une réponse IA via Gemini, avec fallback Groq en cas d'échec.

    Étapes :
    1. Récupération de l'historique conversationnel.
    2. Construction du prompt avec contexte métier (et infos de l'agent si fourni).
    3. Tentative Gemini (gemini-2.5-flash).
    4. En cas d'échec → tentative Groq (llama-3.1-70b-versatile).
    5. Sauvegarde des messages dans l'historique.

    Returns:
        La réponse textuelle de l'IA, ou un message d'erreur par défaut.
    """
    # =========================================================================
    # NIVEAU 1 — DIRECTIVES SYSTÈME STRICTES (Code, inviolable)
    # =========================================================================
    import os
    base_url = os.environ.get('BASE_URL', 'http://localhost:5000').rstrip('/')

    biz_id = business_info.get('id')
    biz_name = business_info.get('nom', 'cette entreprise')

    # Lire les limites du business (définies par master/admin)
    biz_max_tokens = int(business_info.get('max_tokens', 1000))
    biz_tone = business_info.get('response_tone', 'standard')

    # Valeurs par défaut (écrasées si agent actif)
    max_tokens = biz_max_tokens
    response_tone = biz_tone

    # -- Historique récent (cloisonné par business) -------------------------
    history = conversation_repo.get_recent_history(wa_id, biz_id, limit=5)

    # -- Catalogue (source de vérité absolue) -------------------------------
    catalog_str = ""
    if biz_id:
        products = catalog_repo.get_by_business(biz_id, only_available=True)
        if products:
            catalog_str = "CATALOGUE / MENU EXACT (Source de vérité absolue) :\n"
            grouped = {}
            for p in products:
                cat = p['categorie'] or 'Général'
                grouped.setdefault(cat, []).append(p)
                
            needs_product_detail = any(kw in user_message.lower() for kw in ["détail", "composition", "ingrédient", "c'est quoi", "expliquer", "info", "allergi", "piment"])
            
            for cat, items in grouped.items():
                catalog_str += f"[{cat}]\n"
                for p in items:
                    if needs_product_detail and p['description']:
                        desc = f" ({p['description']})"
                    else:
                        desc = ""
                    catalog_str += f"- {p['nom']} : {p['prix']} FCFA{desc}\n"
            catalog_str += (
                "\nINTERDICTION STRICTE : Tu NE DOIS PROPOSER QUE ces produits. "
                "Il t'est STRICTEMENT INTERDIT d'inventer des produits ou des prix "
                "qui ne sont pas dans cette liste.\n"
                f"\n💡 LIEN VERS LE CATALOGUE EN LIGNE (Vitrine) : {base_url}/v/{biz_id}\n"
                "Règle d'usage du lien : Tu peux suggérer 2 ou 3 produits pertinents en texte, "
                "mais indique toujours au client qu'il peut consulter l'intégralité du catalogue avec photos "
                "en cliquant sur ce lien.\n"
            )

    # Vérifier si le client a déjà une commande en attente
    pending_order_str = ""
    last_res = order_repo.get_last_for_user(wa_id)
    if last_res:
        if last_res['statut'] == 'En attente':
            res_dict = dict(last_res)
            pending_order_str = (
                f"ℹ️ INFO : Le client a DÉJÀ une commande EN ATTENTE dans le système ({res_dict['details']} | Date: {res_dict.get('date_heure_debut') or 'Aucune'}).\n"
                "S'il demande à la modifier (ex: ajouter une heure) ou ajouter un article, tu DOIS générer un nouveau tag [RESERVATION:...] avec TOUTES les informations mises à jour.\n"
                "S'il demande juste le statut, dis-lui qu'elle est en attente de validation.\n"
            )
        elif last_res['statut'] in ['Confirmé ✅', 'Prêt']:
            pending_order_str = (
                f"ℹ️ INFO : Le client a une commande récente ayant le statut '{last_res['statut']}' ({last_res['details']}).\n"
                "Ne génère PAS un nouveau tag [RESERVATION:...] pour cette même commande. "
                "Génère un nouveau tag uniquement si le client demande explicitement à passer une NOUVELLE commande complètement différente.\n"
            )

    client_name_str = ""
    client_name = None
    try:
        from app.repositories import client_repo, tag_repo
        client_data = client_repo.get_or_create(biz_id, wa_id)
        if client_data:
            c_dict = dict(client_data)
            nom = c_dict.get('nom')
            display_name = c_dict.get('display_name')
            # Determine which name to use
            if display_name and not display_name.startswith('Client '):
                client_name = display_name
            elif nom and not nom.startswith('Client '):
                client_name = nom
            
            if client_name:
                client_name_str = f"- INFO: Le client s'appelle {client_name}. Utilise son nom pour t'adresser à lui et ne lui demande plus son nom.\n"
    except Exception as e:
        logger.error(f"[AI] Erreur récupération nom client: {e}")

    # Demander le nom au bout de 2 échanges si on ne le connaît pas (et qu'on est dans un process de commande)
    name_request_rule = ""
    if not client_name and len(history) >= 4: # 2 échanges = 4 messages (2 user, 2 bot)
        name_request_rule = "- IMPORTANT: Tu ne connais pas encore le nom du client. S'il initie une commande ou une réservation, demande-lui poliment son nom dans ta réponse (ex: 'Avec plaisir ! Comment puis-je vous appeler ?'). Ne demande pas le nom s'il pose juste une question d'information.\n"

    # Tags dynamiques
    tags_str = ""
    try:
        from app.repositories import tag_repo
        biz_tags = tag_repo.get_business_tags(biz_id)
        if biz_tags:
            tag_lines = []
            for tag in biz_tags:
                desc = tag.get('description', '')
                if desc:
                    words = desc.split()
                    if len(words) > 3:
                        desc = ' '.join(words[:3]) + '...'
                tag_lines.append(f"{tag['name']} ({desc})" if desc else tag['name'])
            
            tags_str = (
                "\n📋 TAGS DISPONIBLES : " + ", ".join(tag_lines) + "\n"
                "Règle d'attribution : Si le contexte correspond à un de ces tags, ajoute-le à la balise RESERVATION avec le format '| TAGS: Tag1, Tag2'.\n"
                "CONTRAINTES STRICTES SUR LES TAGS :\n"
                "1. Si aucun tag ne correspond au message du client, écris OBLIGATOIREMENT : '| TAGS: aucun'\n"
                "2. Ne JAMAIS inventer un tag qui n'est pas dans la liste ci-dessus.\n"
                "3. Applique au MAXIMUM 3 tags par commande, uniquement les plus pertinents.\n"
            )
    except Exception as e:
        logger.error(f"[AI] Erreur récupération tags: {e}")

    # -- Tags techniques obligatoires et Calendrier Dynamique --
    from datetime import timedelta
    import locale
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except:
        pass
    
    now = datetime.now()
    current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Mots-clés déclencheurs pour le contexte temporel
    SCHEDULING_KEYWORDS = [
        "demain", "aujourd'hui", "lundi", "mardi", "mercredi",
        "jeudi", "vendredi", "samedi", "dimanche",
        "heure", "matin", "midi", "soir", "après-midi", "nuit",
        "semaine", "weekend", "prochain", "prochaine",
        "réserver", "rdv", "rendez-vous", "programmer", "planifier",
        "à quelle heure", "disponible", "libre",
        "tantôt", "tout à l'heure", "commande", "commander", "livraison", "ce soir", "ce matin"
    ]
    
    msg_lower = user_message.lower()
    has_pending = last_res and last_res['statut'] == 'En attente'
    needs_scheduling = any(kw in msg_lower for kw in SCHEDULING_KEYWORDS) or has_pending

    agenda_context_str = ""
    calendar_str = ""

    if needs_scheduling:
        from app.services.agenda_service import get_availability_context
        agenda_context_str = get_availability_context(biz_id)
        
        calendar_lines = ["\n📅 CALENDRIER DES 14 PROCHAINS JOURS (Utilise ceci pour trouver la date exacte) :"]
        for i in range(14):
            d = now + timedelta(days=i)
            suffix = " (Aujourd'hui)" if i == 0 else " (Demain)" if i == 1 else ""
            calendar_lines.append(f"- {d.strftime('%A %d %B %Y')} -> {d.strftime('%Y-%m-%d')}{suffix}")
        calendar_str = "\n".join(calendar_lines) + "\n"
        
    # Règle anti-bonjour répétitif
    greeting_rule = ""
    if len(history) > 1:
        greeting_rule = "- 🛑 RÈGLE DE SALUTATION : Tu as déjà discuté avec ce client récemment. NE DIS PLUS 'Bonjour' ou 'Bonsoir', va directement à l'essentiel et réponds de manière fluide.\n"

    system_rules = (
        "⚠️ DIRECTIVES ABSOLUES (priorité maximale) :\n"
        f"📅 Date et heure actuelles du système : {current_time_str}\n"
        f"{calendar_str}"
        f"{pending_order_str}"
        f"{client_name_str}"
        f"{name_request_rule}"
        f"{greeting_rule}"
        "--- GESTION DES NOMS (IMPORTANT) ---\n"
        "- À la première interaction où le client donne son nom (ex: 'Je m'appelle Kofi'), inclus le tag [CLIENT: Son Nom] dans ta réponse.\n"
        "- Si le client demande à changer de nom d'usage ou de surnom (ex: 'Appelle-moi KK', 'Je préfère Boss'), inclus UNIQUEMENT le tag [DISPLAY_NAME: Nouveau Surnom].\n"
        "- Si le client corrige une erreur sur son vrai nom légal (ex: 'Mon vrai nom c'est Koffi avec 2 f'), inclus le tag [NOM_CORRECTION: Vrai Nom].\n"
        "--------------------------------------\n"
        "- Si le client passe une nouvelle commande/réservation, OU s'il ajoute/modifie une information (ex: l'heure, un article) à sa commande déjà en attente, tu DOIS OBLIGATOIREMENT inclure exactement le tag suivant dans ta réponse pour mettre à jour la base de données : "
        "[RESERVATION: résumé de la réservation/commande | DATE: YYYY-MM-DD HH:MM:00 | EMPLOYEE_ID: id_employé | MONTANT: chiffre | PRIORITE: Normale/Haute | TAGS: Tag1, Tag2]\n"
        "- IMPORTANT : Si aucune date ou heure n'est précisée par le client (par exemple une commande pour tout de suite), tu dois mettre DATE: None\n"
        "ATTENTION: Quand tu ajoutes ce tag [RESERVATION:...], tu NE DOIS PAS dire au client que sa demande est 'confirmée'. "
        "Dis-lui qu'elle est 'enregistrée et en attente de validation par notre équipe'. Seul un humain peut la confirmer définitivement.\n"
        "Exemples :\n"
        "1. Avec date : [RESERVATION: Table pour 2 | DATE: 2026-06-28 17:00:00 | EMPLOYEE_ID: 1 | MONTANT: 0 | PRIORITE: Normale | TAGS: VIP]\n"
        "2. Sans date : [RESERVATION: 2 Burgers | DATE: None | EMPLOYEE_ID: None | MONTANT: 25 | PRIORITE: Normale | TAGS: aucun]\n"
        f"{catalog_str}\n\n"          f"{tags_str}\n"
        f"{agenda_context_str}\n"
    )

    # =========================================================================
    # NIVEAU 2 — RÈGLES DE L'ENTREPRISE (Master/Admin, toujours injecté)
    # =========================================================================

    biz_prompt = business_info.get('prompt') or "Tu es un assistant professionnel. Réponds poliment et aide le client."

    # Injection des horaires d'ouverture globaux
    import json
    biz_horaires_str = ""
    raw_biz_horaires = business_info.get('horaires_json')
    if raw_biz_horaires and raw_biz_horaires != '{}':
        try:
            h_data = json.loads(raw_biz_horaires)
            jours = {'lun':'Lundi', 'mar':'Mardi', 'mer':'Mercredi', 'jeu':'Jeudi', 'ven':'Vendredi', 'sam':'Samedi', 'dim':'Dimanche'}
            lignes = []
            for k, v in jours.items():
                plages = h_data.get(k, [])
                if plages and len(plages) >= 2:
                    lignes.append(f"- {v} : {plages[0]} à {plages[1]}")
                else:
                    lignes.append(f"- {v} : Fermé")
            biz_horaires_str = (
                "\nHORAIRES D'OUVERTURE DE L'ENTREPRISE :\n" 
                + "\n".join(lignes) + 
                "\n\n🚨 RÈGLE STRICTE SUR LES HORAIRES :\n"
                "Tu ne DOIS SOUS AUCUN PRÉTEXTE accepter une commande ou réservation pour un jour ou une heure de fermeture.\n"
                "Si le client demande un créneau fermé (ex: 'Fermé' ou en dehors des heures), refuse catégoriquement et propose un autre jour ouvert.\n"
            )
        except Exception:
            pass

    biz_prompt = biz_prompt + "\n" + biz_horaires_str

    # =========================================================================
    # NIVEAU 3 — INCARNATION DE L'AGENT (contexte courant)
    # =========================================================================

    agent_identity_str = ""
    agent_specific_str = ""
    handoff_str = ""

    if agent_info:
        agent_name = agent_info.get('name', 'Assistant')
        agent_role = agent_info.get('role', '')
        agent_system_prompt = agent_info.get('system_prompt', '')
        permissions = agent_info.get('agent_settings_json', '{}')

        # Lire les limites de l'agent
        try:
            if isinstance(permissions, str):
                perm_dict = json.loads(permissions)
            else:
                perm_dict = permissions
            agent_max_tokens = int(perm_dict.get('max_tokens', biz_max_tokens))
            agent_tone = perm_dict.get('response_tone', biz_tone)
            can_escalate = perm_dict.get('can_escalate') in [True, 'true', 'on']
        except Exception:
            agent_max_tokens = biz_max_tokens
            agent_tone = biz_tone
            can_escalate = False

        # Règle de résolution : l'agent peut être plus restrictif, jamais plus permissif
        max_tokens = min(biz_max_tokens, agent_max_tokens)
        response_tone = _resolve_tone(biz_tone, agent_tone)

        logger.debug(
            "[PROMPT_HIERARCHY] biz_max_tokens=%s agent_max_tokens=%s effective=%s "
            "biz_tone=%s agent_tone=%s resolved_tone=%s",
            biz_max_tokens, agent_max_tokens, max_tokens, biz_tone, agent_tone, response_tone
        )

        routing_mode = business_info.get('agent_routing_mode', 'visible')
        if routing_mode == 'visible':
            agent_identity_str = (
                f"Tu es {agent_name}, {agent_role} pour {biz_name}. "
                "Signe tes messages avec ton prénom."
            )
        else:
            agent_identity_str = (
                f"Tu agis au nom de {biz_name}, en te concentrant sur le rôle : {agent_role}. "
                "Ne mentionne jamais ton nom propre."
            )

        agent_specific_str = (
            f"COMPÉTENCES SPÉCIFIQUES À TON RÔLE ({agent_name}) :\n"
            f"{agent_system_prompt}"
        ) if agent_system_prompt else ""

        if can_escalate:
            agent_specific_str += (
                "\n\n⚠️ TRANSFERT HUMAIN AUTORISÉ :\n"
                "- Si le client est en colère, s'il demande explicitement à parler à un humain "
                "(conseiller, gérant, etc.), ou si sa demande dépasse tes compétences, tu DOIS "
                "inclure la balise exacte [TRANSFERT_HUMAIN] à la fin de ta réponse."
            )

        # Injection du contexte de reprise (AVANT l'historique, pour qu'il ait plus de poids)
        if history:
            handoff_str = (
                "[CONTEXTE DE REPRISE] Un collègue a précédemment géré cette conversation. "
                "Voici l'historique. Prends le relais sans répéter ce qui a déjà été dit.\n"
            )
    else:
        logger.debug(
            "[PROMPT_HIERARCHY] biz_max_tokens=%s effective=%s biz_tone=%s resolved_tone=%s (no agent)",
            biz_max_tokens, max_tokens, biz_tone, response_tone
        )

    # -- Injection du Style de Réponse (résolu) -----------------------------
    if response_tone == 'concis':
        tone_instruction = "STYLE DE RÉPONSE : Sois extrêmement concis. Réponds en 2 à 4 phrases courtes maximum.\n"
    elif response_tone == 'detaille':
        tone_instruction = "STYLE DE RÉPONSE : Sois détaillé, pédagogique et exhaustif.\n"
    else:
        tone_instruction = "STYLE DE RÉPONSE : Garde un ton naturel et équilibré.\n"

    # -- Multi-Employés (PREMIUM uniquement) --------------------------------
    multi_emp_str = ""
    plan = business_info.get('plan_abonnement', 'BASIC')
    if plan == 'PREMIUM':
        employees = business_info.get('employees', [])
        if employees:
            emp_lines = []
            for emp in employees:
                nom = emp.get('nom') or emp.get('name', '?')
                poste = emp.get('poste') or emp.get('role', '')
                emp_lines.append(f"  - {nom}" + (f" ({poste})" if poste else ""))
            multi_emp_str = (
                "\nRÈGLES MULTI-EMPLOYÉS :\n"
                "- Lorsqu'un client veut réserver, demande avec quel collaborateur :\n"
                + "\n".join(emp_lines) + "\n"
                "- Tag : [RESERVATION: résumé - avec: NomEmployé | MONTANT: chiffre | PRIORITE: Normale/Haute]\n"
                "- Sans préférence : 'Premier disponible'.\n"
            )

    # =========================================================================
    # ASSEMBLAGE FINAL (ordre = poids décroissant pour le modèle)
    # =========================================================================
    # Niveau 1 en tête → le modèle lui accorde le plus d'attention
    context_instruction = (
        f"{system_rules}\n"
        f"RÈGLES GLOBALES DE L'ENTREPRISE ({biz_name}) :\n{biz_prompt}\n\n"
    )
    if agent_identity_str:
        context_instruction += f"TON IDENTITÉ POUR CETTE SESSION :\n{agent_identity_str}\n\n"
    if agent_specific_str:
        context_instruction += f"{agent_specific_str}\n\n"
    context_instruction += tone_instruction
    context_instruction += multi_emp_str

    # -- Construction du prompt complet ------------------------------------
    full_prompt = context_instruction + "\n"

    # Le contexte de reprise se place AVANT l'historique
    if handoff_str:
        full_prompt += handoff_str

    full_prompt += "--- HISTORIQUE DE LA CONVERSATION ---\n"
    for msg in history:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'user':
            full_prompt += f"Client: {content}\n"
        else:
            full_prompt += f"Assistant: {content}\n"

    full_prompt += (
        "--- FIN DE L'HISTORIQUE ---\n"
        "RAPPEL FINAL : Les directives absolues du début prévalent sur TOUT le reste.\n"
        "Assistant:"
    )

    # -- Tentative Gemini -------------------------------------------------
    try:
        gemini_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=8192
            )
        )
        reply = gemini_response.text.strip()
        reply = re.sub(r'<think>.*?(</think>|$)', '', reply, flags=re.DOTALL).strip()
        if not reply:
            raise Exception("Gemini a retourné une réponse vide après nettoyage du <think>.")
        return reply

    except Exception as e:
        logger.warning("Erreur Gemini : %s", e)

    # -- Fallback Groq ----------------------------------------------------
    try:
        groq_url = "https://api.groq.com/openai/v1/chat/completions"
        groq_headers = {
            "Authorization": f"Bearer {cfg.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        groq_messages = [{"role": "system", "content": context_instruction}]
        for msg in history:
            role = 'assistant' if msg.get('role') == 'assistant' else 'user'
            groq_messages.append({"role": role, "content": msg.get('content', '')})
            
        groq_payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": groq_messages,
            "max_tokens": 2000,
        }

        groq_resp = requests.post(groq_url, json=groq_payload, headers=groq_headers)
        groq_data = groq_resp.json()

        if "choices" in groq_data:
            reply = groq_data["choices"][0]["message"]["content"].strip()
            reply = re.sub(r'<think>.*?(</think>|$)', '', reply, flags=re.DOTALL).strip()
            if not reply:
                raise Exception("Groq a retourné une réponse vide après nettoyage du <think>.")
            return reply

        logger.warning("Groq réponse inattendue : %s", groq_data)
        raise Exception(f"Les deux IA sont indisponibles. Erreur Groq: {groq_data}")

    except Exception as e:
        logger.error("Erreur Groq : %s", e)
        raise Exception(f"Les deux IA sont indisponibles. Dernière erreur: {e}")


def improve_marketing_message(message: str) -> str:
    """
    Améliore un brouillon de message marketing via Gemini, avec fallback Groq (Llama).
    """
    system_prompt = (
        "Tu es un expert en copywriting WhatsApp pour des commerces locaux.\n"
        "Améliore le brouillon de message promotionnel suivant.\n"
        "Rends-le accrocheur, court (max 4-5 phrases), percutant, et ajoute des emojis pertinents.\n"
        "Si le tag {prenom} est présent, conserve-le.\n"
        "Ne renvoie QUE le message amélioré, sans introduction ni explications."
    )
    
    # 1. Tentative Gemini
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=f"{system_prompt}\n\nBrouillon :\n{message}"
        )
        reply = response.text.strip()
        if reply:
            return reply
    except Exception as e:
        logger.warning('Erreur Gemini Marketing Improve: %s', e)

    # 2. Fallback Groq
    try:
        groq_url = "https://api.groq.com/openai/v1/chat/completions"
        groq_headers = {
            "Authorization": f"Bearer {cfg.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        groq_payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Brouillon :\n{message}"}
            ],
            "max_tokens": 1000,
        }
        groq_resp = requests.post(groq_url, json=groq_payload, headers=groq_headers)
        groq_data = groq_resp.json()
        if "choices" in groq_data:
            reply = groq_data["choices"][0]["message"]["content"].strip()
            if reply:
                return reply
    except Exception as e:
        logger.error('Erreur Groq Marketing Improve: %s', e)
        
    raise Exception("Les services d'IA (Gemini et Groq) sont actuellement indisponibles. Vérifiez vos quotas API.")



def generate_bot_prompt_from_answers(nom: str, business_type: str, location: str, bot_tasks: list, tone: str, business_info: str) -> str:
    """Génère un system_prompt initial de qualité à partir des réponses d'onboarding."""
    tasks_text = "\n".join([f"- {t}" for t in bot_tasks]) if isinstance(bot_tasks, list) else bot_tasks
    
    template = f"""Tu es l'assistant virtuel de {nom}, un(e) {business_type} situé(e) à {location}.

Ton rôle principal est de :
{tasks_text}

Tu t'adresses aux clients avec un ton {tone}.

Informations importantes sur l'établissement :
{business_info}

Règles importantes :
- Tu réponds uniquement en rapport avec {nom}
- Si tu ne connais pas la réponse, tu invites le client à contacter directement l'établissement
- Tu ne donnes jamais d'informations sur d'autres établissements
"""
    return template
