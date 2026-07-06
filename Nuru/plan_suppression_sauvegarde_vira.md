# Plan d'Implémentation : Suppression de Compte & Sauvegarde Google Drive
## Vira — SaaS WhatsApp Business

---

## Vue d'ensemble

Ce plan couvre deux fonctionnalités liées à la gestion des données du gérant :

1. **Suppression de compte** — libération immédiate du numéro WhatsApp + nettoyage des données sous 30 jours
2. **Sauvegarde Google Drive** — export automatique des données sur le compte Google du gérant

---

## FONCTIONNALITÉ 1 — Suppression de Compte

### Comportement attendu

```
Numéro WhatsApp libéré    → IMMÉDIATEMENT
Bot désactivé             → IMMÉDIATEMENT
Tokens JWT révoqués       → IMMÉDIATEMENT
Données anonymisées       → sous 30 jours (tâche automatique)
Compte supprimé en DB     → sous 30 jours
```

---

### PHASE 1 — Backend Flask

#### [NEW] `app/api/account.py`

Route de suppression de compte :

```python
DELETE /api/v1/account
Headers: Authorization: Bearer <token>
Body: { "password": "mot_de_passe_actuel" }

Réponse succès :
{
  "message": "Compte supprimé. Votre numéro WhatsApp est libéré.",
  "whatsapp_released": true,
  "data_deletion_date": "2025-02-14"
}
```

Logique interne :

```
1. Vérifier le mot de passe fourni
2. Désabonner le webhook Meta (appel API Meta)
3. Révoquer token_wa en DB (mettre à NULL)
4. Marquer le compte : is_active=False, deletion_scheduled_at=now()+30j
5. Révoquer tous les JWT actifs (blocklist)
6. Envoyer email de confirmation au gérant
7. Retourner succès
```

#### [MODIFY] `app/models/schema.py`

Ajouter colonnes dans la table `businesses` :

```sql
ALTER TABLE businesses ADD COLUMN is_active BOOLEAN DEFAULT 1;
ALTER TABLE businesses ADD COLUMN deletion_scheduled_at DATETIME;
ALTER TABLE businesses ADD COLUMN deletion_reason TEXT;
```

#### [NEW] `app/services/whatsapp_disconnect_service.py`

```python
def disconnect_whatsapp_number(token_wa, phone_number_id):
    """
    Désabonne le numéro WhatsApp Business du webhook Vira.
    Le numéro est immédiatement disponible pour être reconnecté ailleurs.
    """
    response = requests.delete(
        f"https://graph.facebook.com/v18.0/{phone_number_id}/subscribed_apps",
        headers={"Authorization": f"Bearer {decrypt_token(token_wa)}"}
    )
    return response.status_code == 200
```

#### [NEW] `app/tasks/deletion_task.py`

Tâche automatique (APScheduler) — exécutée chaque nuit à minuit :

```python
@scheduler.scheduled_job('cron', hour=0, minute=0)
def process_scheduled_deletions():
    """
    Anonymise et supprime les comptes marqués pour suppression
    dont le délai de 30 jours est écoulé.
    """
    companies_to_delete = Business.query.filter(
        Business.deletion_scheduled_at <= datetime.utcnow(),
        Business.is_active == False
    ).all()

    for company in companies_to_delete:
        # 1. Anonymiser les conversations
        anonymize_conversations(company.id)
        # 2. Anonymiser les clients
        anonymize_clients(company.id)
        # 3. Conserver les transactions (obligation légale 5 ans)
        # 4. Supprimer le profil business
        db.session.delete(company)

    db.session.commit()
```

#### [MODIFY] `app/api/__init__.py`

Enregistrer le blueprint `account`.

---

### PHASE 2 — Application Flutter (Nuru Mobile)

#### [MODIFY] `lib/screens/profile/profile_screen.dart`

Ajouter une section "Zone dangereuse" tout en bas de l'écran Profil :

```
┌─────────────────────────────────────────┐
│  ⚙️  Paramètres du compte               │
│                                         │
│  [...autres paramètres...]              │
│                                         │
│  ──────────────────────────────────     │
│                                         │
│  Zone dangereuse                        │
│                                         │
│  [🗑️  Supprimer mon compte]             │
│  Libère votre numéro WhatsApp           │
│  immédiatement.                         │
│                                         │
└─────────────────────────────────────────┘
```

Le bouton "Supprimer mon compte" est en rouge discret, pas en évidence.

#### [NEW] `lib/screens/profile/delete_account_screen.dart`

Écran de confirmation en 2 étapes :

**Étape 1 — Information**
```
┌─────────────────────────────────────────┐
│  🗑️  Supprimer votre compte             │
│                                         │
│  Ce qui se passe immédiatement :        │
│  ✅ Votre numéro WhatsApp est libéré    │
│  ✅ Votre bot est désactivé             │
│  ✅ Votre accès Vira est révoqué        │
│                                         │
│  Ce qui se passe sous 30 jours :        │
│  ⚠️  Vos données sont supprimées        │
│      définitivement                     │
│                                         │
│  ℹ️  Vos transactions sont conservées   │
│      5 ans (obligation légale)          │
│                                         │
│  ⚠️  Cette action est irréversible      │
│                                         │
│  [Annuler]        [Continuer →]         │
└─────────────────────────────────────────┘
```

**Étape 2 — Confirmation mot de passe**
```
┌─────────────────────────────────────────┐
│  Confirmez votre identité               │
│                                         │
│  Entrez votre mot de passe pour         │
│  confirmer la suppression.              │
│                                         │
│  [🔒 Mot de passe              ]        │
│                                         │
│  [Annuler]  [Supprimer définitivement]  │
└─────────────────────────────────────────┘
```

#### [NEW] `lib/repositories/account_repository.dart`

```dart
Future<void> deleteAccount(String password) async {
  await dio.delete(
    '/account',
    data: {'password': password},
  );
}
```

#### [NEW] `lib/viewmodels/delete_account_notifier.dart`

StateNotifier Riverpod gérant les étapes et l'état de chargement.

---

### Plan de vérification — Suppression

```bash
# 1. Vérifier la déconnexion WhatsApp
# → Envoyer un message au bot après suppression
# → Le bot ne doit plus répondre ✅

# 2. Vérifier la révocation JWT
curl -X GET /api/v1/auth/me \
     -H "Authorization: Bearer <ancien_token>"
# → Doit retourner 401 ✅

# 3. Vérifier le numéro libéré
# → Connecter le numéro à un autre système
# → Doit fonctionner immédiatement ✅

# 4. Vérifier la tâche J+30
# → Manuellement déclencher la tâche
# → Vérifier que les données sont anonymisées en DB ✅
```

---

## FONCTIONNALITÉ 2 — Sauvegarde Google Drive

### Comportement attendu

```
Basic   → Export manuel CSV uniquement
Pro     → Export CSV + Rapport email hebdomadaire
Premium → Backup Google Drive automatique quotidien
           + Rapport email quotidien
           + Export complet JSON
```

---

### PHASE 1 — Backend Flask

#### [MODIFY] `requirements.txt`

```
google-api-python-client==2.111.0
google-auth==2.25.2
google-auth-oauthlib==1.2.0
```

#### [NEW] `app/services/google_drive_service.py`

```python
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import json, os
from datetime import date

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service(google_tokens):
    """
    Construit le service Google Drive depuis les tokens OAuth du gérant.
    """
    creds = Credentials(
        token=google_tokens['access_token'],
        refresh_token=google_tokens['refresh_token'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)

def backup_company_to_drive(company_id, google_tokens):
    """
    Sauvegarde les données d'une entreprise sur son Google Drive.
    """
    # 1. Collecter les données
    data = export_company_data(company_id)
    
    # 2. Écrire le fichier JSON
    filename = f"vira_backup_{company_id}_{date.today()}.json"
    with open(f"/tmp/{filename}", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    # 3. Upload sur Google Drive du gérant
    service = get_drive_service(google_tokens)
    
    # Créer ou retrouver le dossier "Vira Backups"
    folder_id = get_or_create_folder(service, "Vira Backups")
    
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(
        f"/tmp/{filename}",
        mimetype='application/json'
    )
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()
    
    # Nettoyer le fichier temporaire
    os.remove(f"/tmp/{filename}")
    
    return file.get('webViewLink')

def export_company_data(company_id):
    """
    Collecte toutes les données exportables d'une entreprise.
    """
    return {
        "backup_date": str(date.today()),
        "version": "1.0",
        "company": get_company_info(company_id),
        "stats": get_stats_summary(company_id),
        "clients": get_clients_export(company_id),
        "catalog": get_catalog_export(company_id),
        "orders_last_90_days": get_orders_export(company_id, days=90),
    }
```

#### [NEW] `app/api/backup.py`

Routes API pour la gestion de la sauvegarde :

```
GET  /api/v1/backup/google/auth-url
     → Retourne l'URL OAuth Google à ouvrir dans le navigateur

POST /api/v1/backup/google/callback
     → Reçoit le code OAuth, stocke les tokens chiffrés

POST /api/v1/backup/google/trigger
     → Déclenche une sauvegarde manuelle immédiate

GET  /api/v1/backup/google/status
     → Retourne la date de la dernière sauvegarde + lien Drive

DELETE /api/v1/backup/google/disconnect
     → Révoque l'accès Google Drive

GET  /api/v1/backup/export/csv
     → Export CSV des commandes et clients (tous plans)

GET  /api/v1/backup/export/json
     → Export JSON complet (Premium uniquement)
```

#### [MODIFY] `app/models/schema.py`

Ajouter colonnes dans `businesses` :

```sql
ALTER TABLE businesses ADD COLUMN google_access_token TEXT;   -- chiffré
ALTER TABLE businesses ADD COLUMN google_refresh_token TEXT;  -- chiffré
ALTER TABLE businesses ADD COLUMN google_drive_folder_id TEXT;
ALTER TABLE businesses ADD COLUMN last_backup_at DATETIME;
ALTER TABLE businesses ADD COLUMN backup_enabled BOOLEAN DEFAULT 0;
```

#### [NEW] `app/tasks/backup_task.py`

Backup automatique quotidien (APScheduler) :

```python
@scheduler.scheduled_job('cron', hour=23, minute=30)
def daily_backup_premium_companies():
    """
    Sauvegarde automatique des données pour les gérants Premium
    ayant connecté leur Google Drive.
    """
    companies = Business.query.filter_by(
        plan='premium',
        backup_enabled=True,
        is_active=True
    ).all()

    for company in companies:
        try:
            google_tokens = {
                'access_token': decrypt_token(company.google_access_token),
                'refresh_token': decrypt_token(company.google_refresh_token),
            }
            link = backup_company_to_drive(company.id, google_tokens)
            company.last_backup_at = datetime.utcnow()
            db.session.commit()
            
            # Notifier le gérant via Firebase
            send_push_notification(
                company.fcm_token,
                title="✅ Sauvegarde effectuée",
                body=f"Vos données sont sauvegardées sur Google Drive."
            )
        except Exception as e:
            logger.error(f"Backup failed for company {company.id}: {e}")
```

---

### PHASE 2 — Application Flutter (Nuru Mobile)

#### [MODIFY] `lib/screens/profile/profile_screen.dart`

Ajouter une section "Sauvegarde & Export" dans l'écran Profil :

```
┌─────────────────────────────────────────┐
│  💾  Sauvegarde & Export                │
│                                         │
│  Google Drive                           │
│  ┌───────────────────────────────────┐  │
│  │ ✅ Connecté : mon@gmail.com       │  │
│  │ Dernière sauvegarde : aujourd'hui │  │
│  │ 23h30                             │  │
│  └───────────────────────────────────┘  │
│  [Sauvegarder maintenant]               │
│  [Déconnecter Google Drive]             │
│                                         │
│  Export manuel                          │
│  [📊 Exporter commandes (.CSV)]         │
│  [👥 Exporter clients (.CSV)]           │
│  [📦 Export complet (.JSON)] 🔒 Premium │
│                                         │
└─────────────────────────────────────────┘
```

#### [NEW] `lib/screens/profile/backup_screen.dart`

Écran dédié à la gestion de la sauvegarde :

```
┌─────────────────────────────────────────┐
│  ← Sauvegarde Google Drive              │
│                                         │
│  🟢 Google Drive connecté               │
│  mon.compte@gmail.com                   │
│                                         │
│  📁 Dossier : "Vira Backups"            │
│  🕐 Dernière sauvegarde :               │
│     Aujourd'hui à 23h30                 │
│  📅 Fréquence : Quotidienne (23h30)     │
│                                         │
│  [🔄 Sauvegarder maintenant]            │
│                                         │
│  ──────────────────────────────────     │
│                                         │
│  Ce qui est sauvegardé :               │
│  ✅ Profil boutique                     │
│  ✅ Liste des clients                   │
│  ✅ Commandes (90 derniers jours)       │
│  ✅ Catalogue produits                  │
│  ✅ Statistiques                        │
│  ❌ Conversations WhatsApp (privées)    │
│                                         │
│  [🔗 Ouvrir dans Google Drive]          │
│  [❌ Déconnecter Google Drive]          │
│                                         │
└─────────────────────────────────────────┘
```

#### [NEW] `lib/repositories/backup_repository.dart`

```dart
// Déclencher une sauvegarde manuelle
Future<String> triggerBackup() async {
  final response = await dio.post('/backup/google/trigger');
  return response.data['drive_link'];
}

// Récupérer le statut de la dernière sauvegarde
Future<BackupStatus> getBackupStatus() async {
  final response = await dio.get('/backup/google/status');
  return BackupStatus.fromJson(response.data);
}

// Export CSV
Future<void> exportCSV(String type) async {
  final response = await dio.get(
    '/backup/export/csv',
    queryParameters: {'type': type}, // 'orders' ou 'clients'
  );
  // Sauvegarder dans les téléchargements du téléphone
  await saveToDownloads(response.data, '$type.csv');
}
```

#### [NEW] `lib/viewmodels/backup_notifier.dart`

StateNotifier Riverpod gérant l'état de la sauvegarde (chargement, succès, erreur).

---

### Plan de vérification — Sauvegarde

```
1. Connecter Google Drive depuis l'app
   → Vérifier que le dossier "Vira Backups" est créé ✅

2. Déclencher une sauvegarde manuelle
   → Vérifier que le fichier JSON apparaît dans Google Drive ✅
   → Vérifier que le fichier contient des données correctes ✅

3. Simuler la tâche automatique nocturne
   → Déclencher manuellement le scheduler
   → Vérifier la notification push "Sauvegarde effectuée" ✅

4. Tester l'export CSV
   → Télécharger le fichier depuis l'app
   → Ouvrir dans Excel/Sheets → données lisibles ✅

5. Tester Basic avec export JSON
   → Doit retourner 403 (réservé Premium) ✅
```

---

## Récapitulatif des fichiers à créer/modifier

### Backend Flask

| Fichier | Action | Priorité |
|---|---|---|
| `app/api/account.py` | NOUVEAU | 🔴 Critique |
| `app/api/backup.py` | NOUVEAU | 🟡 Important |
| `app/services/whatsapp_disconnect_service.py` | NOUVEAU | 🔴 Critique |
| `app/services/google_drive_service.py` | NOUVEAU | 🟡 Important |
| `app/tasks/deletion_task.py` | NOUVEAU | 🔴 Critique |
| `app/tasks/backup_task.py` | NOUVEAU | 🟡 Important |
| `app/models/schema.py` | MODIFIER | 🔴 Critique |
| `app/api/__init__.py` | MODIFIER | 🔴 Critique |
| `requirements.txt` | MODIFIER | 🟡 Important |
| `.env` | MODIFIER | 🟡 Important |

### Flutter (Nuru Mobile)

| Fichier | Action | Priorité |
|---|---|---|
| `lib/screens/profile/profile_screen.dart` | MODIFIER | 🔴 Critique |
| `lib/screens/profile/delete_account_screen.dart` | NOUVEAU | 🔴 Critique |
| `lib/screens/profile/backup_screen.dart` | NOUVEAU | 🟡 Important |
| `lib/repositories/account_repository.dart` | NOUVEAU | 🔴 Critique |
| `lib/repositories/backup_repository.dart` | NOUVEAU | 🟡 Important |
| `lib/viewmodels/delete_account_notifier.dart` | NOUVEAU | 🔴 Critique |
| `lib/viewmodels/backup_notifier.dart` | NOUVEAU | 🟡 Important |
| `lib/core/router.dart` | MODIFIER | 🔴 Critique |

---

## Variables d'environnement à ajouter

```bash
# .env
GOOGLE_CLIENT_ID=votre_client_id_google
GOOGLE_CLIENT_SECRET=votre_client_secret_google
GOOGLE_REDIRECT_URI=https://votre-domaine.com/api/v1/backup/google/callback
```

---

## Ordre d'implémentation recommandé

```
Semaine 1 :
├── Suppression compte (Backend)
│   ├── schema.py (nouvelles colonnes)
│   ├── whatsapp_disconnect_service.py
│   ├── account.py (route DELETE)
│   └── deletion_task.py (APScheduler)
└── Suppression compte (Flutter)
    ├── delete_account_screen.dart
    ├── account_repository.dart
    └── delete_account_notifier.dart

Semaine 2 :
├── Sauvegarde Google Drive (Backend)
│   ├── google_drive_service.py
│   ├── backup.py (routes API)
│   └── backup_task.py (APScheduler)
└── Sauvegarde Google Drive (Flutter)
    ├── backup_screen.dart
    ├── backup_repository.dart
    └── backup_notifier.dart
```

---

*Document généré pour le projet Vira — Version 1.0*
