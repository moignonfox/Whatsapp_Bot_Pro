library;

/// Gestion des plans d'abonnement et des fonctionnalités associées.
/// Utilisé partout dans l'app pour activer/désactiver des features selon le plan.

enum SubscriptionPlan { basic, pro, premium }

extension SubscriptionPlanExtension on SubscriptionPlan {
  String get label {
    switch (this) {
      case SubscriptionPlan.basic:
        return 'BASIC';
      case SubscriptionPlan.pro:
        return 'PRO';
      case SubscriptionPlan.premium:
        return 'PREMIUM';
    }
  }

  bool get isPro => this == SubscriptionPlan.pro || this == SubscriptionPlan.premium;
  bool get isPremium => this == SubscriptionPlan.premium;

  static SubscriptionPlan fromString(String value) {
    switch (value.toUpperCase()) {
      case 'PRO':
        return SubscriptionPlan.pro;
      case 'PREMIUM':
        return SubscriptionPlan.premium;
      default:
        return SubscriptionPlan.basic;
    }
  }
}

/// Définit toutes les fonctionnalités de l'application et leur niveau d'accès minimum.
enum AppFeature {
  dashboard,        // BASIC
  commandes,        // BASIC
  chat,             // BASIC
  catalogue,        // BASIC
  statistiques,     // PRO
  paiements,        // PRO
  campagnes,        // PRO
  multiEmployes,    // PREMIUM
  crm,              // PREMIUM
  marketingAvance,  // PREMIUM
}

extension AppFeatureExtension on AppFeature {
  SubscriptionPlan get requiredPlan {
    switch (this) {
      case AppFeature.dashboard:
      case AppFeature.commandes:
      case AppFeature.chat:
      case AppFeature.catalogue:
        return SubscriptionPlan.basic;
      case AppFeature.statistiques:
      case AppFeature.campagnes:
        return SubscriptionPlan.pro;
      case AppFeature.paiements:
      case AppFeature.multiEmployes:
      case AppFeature.crm:
      case AppFeature.marketingAvance:
        return SubscriptionPlan.premium;
    }
  }

  String get displayName {
    switch (this) {
      case AppFeature.dashboard:
        return 'Tableau de bord';
      case AppFeature.commandes:
        return 'Commandes';
      case AppFeature.chat:
        return 'Messages WhatsApp';
      case AppFeature.catalogue:
        return 'Catalogue';
      case AppFeature.statistiques:
        return 'Statistiques avancées';
      case AppFeature.paiements:
        return 'Paiements / Finance';
      case AppFeature.campagnes:
        return 'Campagnes marketing';
      case AppFeature.multiEmployes:
        return 'Multi-employés';
      case AppFeature.crm:
        return 'CRM complet';
      case AppFeature.marketingAvance:
        return 'Marketing avancé';
    }
  }

  bool isAvailableFor(SubscriptionPlan plan) {
    final required = requiredPlan;
    if (required == SubscriptionPlan.basic) return true;
    if (required == SubscriptionPlan.pro) return plan.isPro;
    if (required == SubscriptionPlan.premium) return plan.isPremium;
    return false;
  }
}
