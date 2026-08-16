"""
schema.py — Création et migration du schéma de la base de données.

Centralise la définition des tables et les mises à jour de schéma
pour que tous les modules partagent une source de vérité unique.
"""

import os
import sqlite3


def get_db_path() -> str:
    """Renvoie le chemin absolu vers le fichier de base de données."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'data',
        'bot_memory.db',
    )


def init_db() -> None:
    """Crée les tables nécessaires si elles n'existent pas encore."""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Activer WAL (Write-Ahead Logging) : réduit fortement les "database is locked"
    # en cas de lectures/écritures simultanées (multi-worker Gunicorn).
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")  # Cohérent avec WAL, plus rapide

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            wa_id     TEXT,
            business_id TEXT,
            agent_id  INTEGER,
            role      TEXT,
            content   TEXT,
            timestamp DATETIME,
            is_read   INTEGER DEFAULT 0,
            message_type TEXT DEFAULT 'text',
            media_url TEXT,
            message_status TEXT DEFAULT 'sent',
            meta_message_id TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            id                TEXT PRIMARY KEY,
            nom               TEXT,
            whatsapp_phone_id TEXT,
            token_wa          TEXT,
            password          TEXT,
            prompt            TEXT,
            msg_confirm       TEXT,
            msg_cancel        TEXT,
            msg_ready         TEXT,
            human_mode        TEXT DEFAULT '{}',
            business_type     TEXT DEFAULT 'restaurant',
            plan_abonnement   TEXT DEFAULT 'FREE',
            is_active         INTEGER DEFAULT 1,
            owner_phone       TEXT,
            drip_j3_enabled   INTEGER DEFAULT 0,
            drip_j3_msg       TEXT,
            agent_routing_mode TEXT DEFAULT 'visible',
            debounce_delay    INTEGER DEFAULT 3,
            requested_bot_phone TEXT,
            vitrine_color     TEXT DEFAULT '#5b6af0',
            vitrine_logo_url  TEXT,
            vitrine_cover_url TEXT,
            vitrine_description TEXT,
            fcm_token         TEXT,
            email             TEXT,
            owner_name        TEXT,
            devise            TEXT DEFAULT 'FCFA',
            is_approved       INTEGER DEFAULT 0,
            date_debut_abonnement DATETIME DEFAULT CURRENT_TIMESTAMP,
            date_fin_abonnement   DATETIME,
            deletion_scheduled_at DATETIME,
            deletion_reason       TEXT,
            google_access_token   TEXT,
            google_refresh_token  TEXT,
            google_drive_folder_id TEXT,
            last_backup_at        DATETIME,
            backup_enabled        INTEGER DEFAULT 0,
            daily_report_time     TEXT DEFAULT '19:00',
            status                TEXT DEFAULT 'active',
            archived_at           DATETIME
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL,
            nom         TEXT NOT NULL,
            poste       TEXT,
            actif       INTEGER DEFAULT 1,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT,
            wa_id       TEXT,
            details     TEXT,
            statut      TEXT DEFAULT 'En attente',
            priorite    TEXT DEFAULT 'Normale',
            montant     INTEGER DEFAULT 0,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            business_id      TEXT,
            wa_id            TEXT,
            nom              TEXT,
            platform         TEXT DEFAULT 'whatsapp',
            date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (business_id, wa_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sectors (
            id               TEXT PRIMARY KEY,
            name             TEXT,
            vocab            TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL,
            categorie   TEXT DEFAULT 'Général',
            nom         TEXT NOT NULL,
            description TEXT,
            prix        INTEGER DEFAULT 0,
            disponible  INTEGER DEFAULT 1,
            image_url   TEXT,
            is_visible  INTEGER DEFAULT 1,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT,
            system_prompt TEXT,
            intent_keywords TEXT,
            permissions_json TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    """)


    # --- Migration V10: Tags System ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL,
            type TEXT DEFAULT 'Commande', -- 'Commande' ou 'Client'
            name TEXT NOT NULL,
            color TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_tags (
            order_id INTEGER,
            tag_id INTEGER,
            FOREIGN KEY (order_id) REFERENCES reservations (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
            PRIMARY KEY (order_id, tag_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_tags (
            wa_id TEXT,
            business_id TEXT,
            tag_id INTEGER,
            FOREIGN KEY (wa_id, business_id) REFERENCES clients (wa_id, business_id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
            PRIMARY KEY (wa_id, business_id, tag_id)
        )
    ''')

    # Table blocklist JWT — stocke les tokens révoqués (logout)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jwt_blocklist (
            jti        TEXT PRIMARY KEY,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications_master (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            type       TEXT NOT NULL,
            title      TEXT NOT NULL,
            message    TEXT NOT NULL,
            business_id TEXT,
            is_read    INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        )
    ''')

    # Table anti-rejeu webhook Meta — stocke les wam_id 24h
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS webhook_seen_ids (
            wam_id     TEXT PRIMARY KEY,
            seen_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL,
            title TEXT,
            message TEXT,
            target TEXT,
            status TEXT DEFAULT 'Planifiée',
            scheduled_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            recipients_count INTEGER DEFAULT 0,
            sent_count INTEGER DEFAULT 0,
            read_count INTEGER DEFAULT 0,
            reply_count INTEGER DEFAULT 0,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    ''')

    # --- Table channels (Multi-Canal / Workspace Pattern) ---
    # SECURITE : Le champ `config` est un JSON qui peut contenir des tokens
    # sensibles (ex: token_wa Meta). Il NE DOIT PAS être renvoyé tel quel
    # dans les réponses API. Filtrer les champs sensibles avant tout renvoi.
    # Pour une sécurité maximale en production, chiffrer ce champ via
    # la clé SECRET_KEY de l'environnement avant écriture.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id  TEXT NOT NULL,
            type         TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'not_connected',
            config       TEXT DEFAULT '{}',
            connected_at DATETIME,
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    """)
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_channels_business_type ON channels (business_id, type)"
    )

    conn.commit()
    conn.close()


def update_schema() -> None:
    """Applique les migrations de schéma (ajout de colonnes manquantes)."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN vitrine_cover_url TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN vitrine_description TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE reservations ADD COLUMN montant INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà

    try:
        cursor.execute("ALTER TABLE reservations ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà
        
    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN adresse TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN site_web TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE history ADD COLUMN business_id TEXT")
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà

    try:
        cursor.execute("ALTER TABLE history ADD COLUMN agent_id INTEGER")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE history ADD COLUMN is_read INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE history ADD COLUMN message_type TEXT DEFAULT 'text'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE history ADD COLUMN media_url TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE history ADD COLUMN message_status TEXT DEFAULT 'sent'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE history ADD COLUMN meta_message_id TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN human_mode TEXT DEFAULT '{}'")
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN business_type TEXT DEFAULT 'restaurant'")
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN plan_abonnement TEXT DEFAULT 'FREE'")
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà

    # Migration des anciens plans (V1) vers les nouveaux plans stratégiques (V2)
    try:
        cursor.execute("UPDATE businesses SET plan_abonnement = 'DISCOVERY' WHERE plan_abonnement = 'BASIC'")
        cursor.execute("UPDATE businesses SET plan_abonnement = 'GROWTH' WHERE plan_abonnement = 'PRO'")
        cursor.execute("UPDATE businesses SET plan_abonnement = 'SCALE' WHERE plan_abonnement = 'PREMIUM'")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN is_active INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà
        
    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN owner_phone TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN drip_j3_enabled INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN drip_j3_msg TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN agent_routing_mode TEXT DEFAULT 'visible'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN debounce_delay INTEGER DEFAULT 3")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN horaires_json TEXT DEFAULT '{}'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN fcm_token TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN date_debut_abonnement DATETIME DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN date_fin_abonnement DATETIME")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN owner_name TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN devise TEXT DEFAULT 'FCFA'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN is_approved INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN deletion_scheduled_at DATETIME")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN deletion_reason TEXT")
    except sqlite3.OperationalError:
        pass

    # Colonnes CinetPay multi-tenant (chiffrées via crypto_service)
    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN cinetpay_site_id TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN cinetpay_apikey TEXT")
    except sqlite3.OperationalError:
        pass

    # Google Drive Backup
    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN google_access_token TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN google_refresh_token TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN google_drive_folder_id TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN last_backup_at DATETIME")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN backup_enabled INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN daily_report_time TEXT DEFAULT '19:00'")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN status TEXT DEFAULT 'active'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN archived_at DATETIME")
    except sqlite3.OperationalError:
        pass

    # Blocklist JWT
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jwt_blocklist (
            jti        TEXT PRIMARY KEY,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Notifications Master
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications_master (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            type       TEXT NOT NULL,
            title      TEXT NOT NULL,
            message    TEXT NOT NULL,
            business_id TEXT,
            is_read    INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        )
    ''')

    # Anti-rejeu webhook Meta
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS webhook_seen_ids (
            wam_id     TEXT PRIMARY KEY,
            seen_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migration V9 : Renommage de permissions_json en agent_settings_json pour plus de clarté
    try:
        cursor.execute("ALTER TABLE ai_agents RENAME COLUMN permissions_json TO agent_settings_json")
        print("Migration: colonne 'permissions_json' renommée en 'agent_settings_json' dans 'ai_agents'.")
    except sqlite3.OperationalError:
        pass

    # Table employees (Multi-Employés — offre PREMIUM)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL,
            nom         TEXT NOT NULL,
            poste       TEXT,
            actif       INTEGER DEFAULT 1,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    """)

    # Table ai_agents (Multi-Employé Agent IA)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT,
            system_prompt TEXT,
            intent_keywords TEXT,
            agent_settings_json TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    """)

    # Table products (Catalogue de l'IA)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL,
            categorie   TEXT DEFAULT 'Général',
            nom         TEXT NOT NULL,
            description TEXT,
            prix        INTEGER DEFAULT 0,
            disponible  INTEGER DEFAULT 1,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    """)

    # Table global_settings (Paramètres Master)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Initialisation des paramètres par défaut
    cursor.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('max_input_basic', '500')")
    cursor.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('max_input_pro', '1000')")
    cursor.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('max_input_premium', '3000')")
    
    # Quotas de consommation IA
    cursor.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('quota_messages_basic', '500')")
    cursor.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('quota_messages_pro', '2000')")
    cursor.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('quota_messages_premium', '10000')")
    cursor.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('overage_behavior', 'FALLBACK')")

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN categorie TEXT DEFAULT 'Général'")
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN duree_minutes INTEGER DEFAULT 30")
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà

    # Migration de la table clients pour isoler par société (business_id)
    cursor.execute("PRAGMA table_info(clients)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'business_id' not in columns:
        cursor.execute("ALTER TABLE clients RENAME TO clients_old")
        cursor.execute("""
            CREATE TABLE clients (
                business_id      TEXT,
                wa_id            TEXT,
                nom              TEXT,
                date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (business_id, wa_id)
            )
        """)
        cursor.execute("""
            INSERT INTO clients (business_id, wa_id, nom, date_inscription)
            SELECT '', wa_id, nom, date_inscription FROM clients_old
        """)
        cursor.execute("DROP TABLE clients_old")


    # --- Migration V10: Tags System ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL,
            type TEXT DEFAULT 'Commande', -- 'Commande' ou 'Client'
            name TEXT NOT NULL,
            color TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_tags (
            order_id INTEGER,
            tag_id INTEGER,
            FOREIGN KEY (order_id) REFERENCES reservations (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
            PRIMARY KEY (order_id, tag_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_tags (
            wa_id TEXT,
            business_id TEXT,
            tag_id INTEGER,
            FOREIGN KEY (wa_id, business_id) REFERENCES clients (wa_id, business_id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
            PRIMARY KEY (wa_id, business_id, tag_id)
        )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL,
            title TEXT,
            message TEXT,
            target TEXT,
            status TEXT DEFAULT 'Planifiée',
            scheduled_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            recipients_count INTEGER DEFAULT 0,
            sent_count INTEGER DEFAULT 0,
            read_count INTEGER DEFAULT 0,
            reply_count INTEGER DEFAULT 0,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    ''')

    # --- Table channels (Multi-Canal / Workspace Pattern) ---
    # SECURITE : Le champ `config` est un JSON qui peut contenir des tokens
    # sensibles (ex: token_wa Meta). Il NE DOIT PAS être renvoyé tel quel
    # dans les réponses API. Filtrer les champs sensibles avant tout renvoi.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id  TEXT NOT NULL,
            type         TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'not_connected',
            config       TEXT DEFAULT '{}',
            connected_at DATETIME,
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
    """)
    try:
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_channels_business_type ON channels (business_id, type)"
        )
    except Exception:
        pass

    # --- Migration Douce V11 : whatsapp_phone_id → channels ---
    # Pour chaque business ayant un numéro WhatsApp configuré,
    # on crée une ligne dans `channels` si elle n'existe pas encore.
    # Idempotent : sûr de relancer autant de fois que nécessaire.
    # Les colonnes whatsapp_phone_id et token_wa sont CONSERVÉES dans
    # `businesses` pour la rétrocompatibilité (supprimer seulement
    # quand tout est stable en production).
    import json as _json
    cursor.execute("""
        SELECT id, whatsapp_phone_id, token_wa
        FROM businesses
        WHERE whatsapp_phone_id IS NOT NULL
          AND whatsapp_phone_id != ''
    """)
    businesses_to_migrate = cursor.fetchall()
    migrated_count = 0
    for (biz_id, phone_id, token_wa) in businesses_to_migrate:
        cursor.execute(
            "SELECT id FROM channels WHERE business_id = ? AND type = 'whatsapp'",
            (biz_id,)
        )
        if cursor.fetchone() is None:
            config_data = _json.dumps({
                "whatsapp_phone_id": phone_id,
                "token_wa": token_wa or ""
            })
            cursor.execute("""
                INSERT INTO channels (business_id, type, status, config, connected_at)
                VALUES (?, 'whatsapp', 'connected', ?, CURRENT_TIMESTAMP)
            """, (biz_id, config_data))
            migrated_count += 1
    if migrated_count > 0:
        print(f"Migration V11: {migrated_count} compte(s) WhatsApp migrés vers la table 'channels'.")

    conn.commit()
    conn.close()
