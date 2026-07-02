# Tâches pour MyBot Mobile (Nuru) - Session 6 (WebSockets / Temps Réel)

- [x] **1. Configuration Socket.IO**
  - [x] Ajouter `socket_io_client` dans `pubspec.yaml`
  - [x] Créer `lib/core/api/socket_client.dart`
  - [x] Gérer l'authentification et la reconnexion avec le JWT

- [x] **2. Temps Réel : Chat**
  - [x] Écouter l'événement `nouveau_message` dans `ChatDetailNotifier`
  - [x] Écouter l'événement `human_mode_toggled` pour basculer le mode

- [x] **3. Temps Réel : Commandes**
  - [x] Écouter l'événement `nouvelle_commande` dans `TodayNotifier`
  - [x] Écouter l'événement `statut_commande` dans `TodayNotifier`
  - [x] Rafraîchir l'interface sans Pull-to-Refresh manuel
