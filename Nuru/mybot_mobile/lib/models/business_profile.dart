class BusinessProfile {
  final String id;
  final String nom;
  final String ownerName;
  final String planAbonnement;
  final bool isActive;
  final bool isApproved;
  final String prompt;
  final String msgConfirm;
  final String vitrineColor;
  final String horairesJson;
  final String email;
  final String ownerPhone;
  final String requestedBotPhone;
  final String devise;
  final String dateDebutAbonnement;
  final String dateFinAbonnement;

  BusinessProfile({
    required this.id,
    required this.nom,
    required this.ownerName,
    required this.planAbonnement,
    required this.isActive,
    required this.isApproved,
    required this.prompt,
    required this.msgConfirm,
    required this.vitrineColor,
    required this.horairesJson,
    required this.email,
    required this.ownerPhone,
    required this.requestedBotPhone,
    required this.devise,
    required this.dateDebutAbonnement,
    required this.dateFinAbonnement,
  });

  factory BusinessProfile.fromJson(Map<String, dynamic> json) {
    return BusinessProfile(
      id: json['id'] ?? '',
      nom: json['nom'] ?? '',
      ownerName: json['owner_name'] ?? '',
      planAbonnement: json['plan_abonnement'] ?? 'BASIC',
      isActive: json['is_active'] == 1 || json['is_active'] == true,
      isApproved: json['is_approved'] == 1 || json['is_approved'] == true,
      prompt: json['prompt'] ?? '',
      msgConfirm: json['msg_confirm'] ?? '',
      vitrineColor: json['vitrine_color'] ?? '#5b6af0',
      horairesJson: json['horaires_json'] ?? '{}',
      email: json['email'] ?? '',
      ownerPhone: json['owner_phone'] ?? '',
      requestedBotPhone: json['requested_bot_phone'] ?? '',
      devise: json['devise'] ?? 'FCFA',
      dateDebutAbonnement: json['date_debut_abonnement'] ?? '',
      dateFinAbonnement: json['date_fin_abonnement'] ?? '',
    );
  }

  BusinessProfile copyWith({
    String? nom,
    String? ownerName,
    String? planAbonnement,
    bool? isActive,
    bool? isApproved,
    String? prompt,
    String? msgConfirm,
    String? vitrineColor,
    String? horairesJson,
    String? email,
    String? ownerPhone,
    String? requestedBotPhone,
    String? devise,
    String? dateDebutAbonnement,
    String? dateFinAbonnement,
  }) {
    return BusinessProfile(
      id: id,
      nom: nom ?? this.nom,
      ownerName: ownerName ?? this.ownerName,
      planAbonnement: planAbonnement ?? this.planAbonnement,
      isActive: isActive ?? this.isActive,
      isApproved: isApproved ?? this.isApproved,
      prompt: prompt ?? this.prompt,
      msgConfirm: msgConfirm ?? this.msgConfirm,
      vitrineColor: vitrineColor ?? this.vitrineColor,
      horairesJson: horairesJson ?? this.horairesJson,
      email: email ?? this.email,
      ownerPhone: ownerPhone ?? this.ownerPhone,
      requestedBotPhone: requestedBotPhone ?? this.requestedBotPhone,
      devise: devise ?? this.devise,
      dateDebutAbonnement: dateDebutAbonnement ?? this.dateDebutAbonnement,
      dateFinAbonnement: dateFinAbonnement ?? this.dateFinAbonnement,
    );
  }
}
