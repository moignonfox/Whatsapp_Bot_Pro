# Audit Mobile MyBot : Stratégie de Portage

Ce document présente l'audit complet du dashboard web "MyBot" en vue d'une transition vers une application mobile (iOS/Android ou PWA). 
L'objectif est d'adapter l'outil aux commerçants en mobilité : ceux-ci ont besoin d'être alertés en temps réel, de consulter rapidement leur activité, et de répondre instantanément sans être derrière un ordinateur.

> [!TIP]
> **Philosophie Mobile-First :** L'application mobile ne doit pas être une simple copie du site web. Elle doit se concentrer sur **l'action rapide** (répondre à un client, accepter une commande) et **les alertes** (notifications push). Les tâches complexes de configuration doivent être reléguées au second plan ou conservées sur la version web.

---

## 1. Chat en Direct (Live Chat)
- **Fonctionnalité :** Reprendre la main sur l'IA pour converser avec les clients via WhatsApp.
- **Priorité :** 🔴 **Indispensable**
- **Stratégie Mobile :** Doit être le **coeur** de l'application mobile (similaire à WhatsApp Business).
- **Adaptations :** 
  - **Notifications Push :** Notification immédiate si l'IA demande l'intervention humaine ou si le client veut parler à un humain.
  - **Interface :** Vue de messagerie plein écran, clavier natif, bouton "Céder à l'IA" ou "Prendre la main" bien visible et flottant.
  - **Action :** Simplifiée au maximum. Les commerçants doivent pouvoir répondre d'une seule main.

## 2. Commandes & Réservations (Agenda / Orders)
- **Fonctionnalité :** Consulter la liste des commandes du jour et l'agenda des réservations.
- **Priorité :** 🔴 **Indispensable**
- **Stratégie Mobile :** Optimisée pour le "Coup d'œil" et les actions rapides.
- **Adaptations :**
  - **Interface :** Au lieu d'un grand tableau (orders.html) ou d'un calendrier complexe (agenda.html), créer une vue "Aujourd'hui" sous forme de timeline ou de cartes (Cards).
  - **Gestes tactiles :** Swiper vers la droite pour "Marquer comme prêt", swiper vers la gauche pour "Annuler".
  - **Notifications Push :** Alerte sonore (avec le choix du son configuré) pour chaque nouvelle réservation ou commande confirmée.

## 3. Tableau de Bord (Dashboard / Admin)
- **Fonctionnalité :** Statistiques (CA, nombre de commandes, clients actifs).
- **Priorité :** 🟡 **Utile**
- **Stratégie Mobile :** Simplifiée.
- **Adaptations :**
  - **Interface :** Afficher uniquement 3 à 4 métriques clés "Du jour" en haut de l'écran d'accueil (ex: Commandes du jour, CA du jour). 
  - **Graphiques complexes :** Les graphiques de tendance doivent être cachés derrière un onglet "Statistiques" spécifique ou gardés uniquement pour le web.

## 4. CRM & Clients (Clients)
- **Fonctionnalité :** Liste des clients, historiques de leurs commandes et notes.
- **Priorité :** 🟡 **Utile**
- **Stratégie Mobile :** Consultative.
- **Adaptations :**
  - **Interface :** Une liste de contacts avec une barre de recherche en haut. 
  - **Action :** Cliquer sur un client ouvre un "Tiroir" (Bottom Sheet) avec son profil rapide (Nom, Tél, Commandes totales) et un bouton "Envoyer un message".

## 5. Catalogue & Produits (Catalog)
- **Fonctionnalité :** Ajouter, modifier, supprimer des produits ou services.
- **Priorité :** 🟡 **Utile**
- **Stratégie Mobile :** Simplifiée. L'ajout d'un catalogue entier de 50 articles se fait sur PC, mais la modification d'une rupture de stock doit se faire sur mobile.
- **Adaptations :**
  - **Interface :** Liste des produits sous forme de cartes.
  - **Action clé :** Un bouton "Toggle" (Switch) pour passer rapidement un produit en "Rupture de stock" d'un simple toucher.
  - **Ajout :** Permettre de prendre une photo directement depuis l'appareil photo du téléphone pour ajouter un nouveau produit rapidement.

## 6. Marketing & Campagnes (Marketing)
- **Fonctionnalité :** Lancer des campagnes de messages groupés.
- **Priorité :** 🟢 **Optionnelle**
- **Stratégie Mobile :** Reléguée dans un menu secondaire, voire ignorée. La création d'une campagne de marketing nécessite de la réflexion et se fait généralement assis à un bureau.
- **Adaptations :** Interface très basique si présente, mais la priorité est faible.

## 7. Paramètres, IA & Équipe (Settings, Agents, Employees, Vitrine)
- **Fonctionnalité :** Régler le prompt de l'IA, les heures d'ouverture de l'équipe, la page vitrine, les clés API.
- **Priorité :** 🟢 **Optionnelle**
- **Stratégie Mobile :** Simplifiée ou absente.
- **Adaptations :**
  - La gestion des **Horaires** (récemment implémentée) peut être utile sur mobile si le restaurateur veut fermer la boutique en urgence (ex: inondation). Il faut donc juste un bouton "Fermeture exceptionnelle".
  - Les réglages du prompt IA et des configurations complexes peuvent être réservés à l'ordinateur de bureau.

---

## Résumé de l'Architecture Mobile Recommandée (Navigation)

Une application mobile efficace pour MyBot utiliserait une **Bottom Navigation Bar** avec 4 onglets :

1. 📥 **Boîte de réception (Chat)** : Par défaut. Chat avec les clients, notifications d'intervention IA.
2. 🗓️ **Aujourd'hui (Commandes/Agenda)** : Timeline des réservations et commandes à préparer aujourd'hui.
3. 📦 **Catalogue** : Pour la gestion rapide des stocks (bouton rupture de stock).
4. ⚙️ **Menu / Profil** : Statistiques, fermeture d'urgence, réglages simples.

> [!IMPORTANT]  
> **L'avantage principal de l'App Mobile : Les Push Notifications.**  
> Le fait d'avoir une App native (ou PWA bien configurée) permet de réveiller le téléphone du restaurateur (même écran verrouillé) lorsqu'une réservation urgente arrive ou que l'IA a besoin d'aide. C'est l'argument de vente numéro 1 de la version mobile.
