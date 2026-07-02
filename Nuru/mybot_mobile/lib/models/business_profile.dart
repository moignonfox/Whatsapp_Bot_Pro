class BusinessProfile {
  final String id;
  final String nom;
  final String planAbonnement;
  final bool isActive;
  final String prompt;
  final String msgConfirm;
  final String vitrineColor;
  final String horairesJson;

  BusinessProfile({
    required this.id,
    required this.nom,
    required this.planAbonnement,
    required this.isActive,
    required this.prompt,
    required this.msgConfirm,
    required this.vitrineColor,
    required this.horairesJson,
  });

  factory BusinessProfile.fromJson(Map<String, dynamic> json) {
    return BusinessProfile(
      id: json['id'] ?? '',
      nom: json['nom'] ?? '',
      planAbonnement: json['plan_abonnement'] ?? 'BASIC',
      isActive: json['is_active'] == 1 || json['is_active'] == true,
      prompt: json['prompt'] ?? '',
      msgConfirm: json['msg_confirm'] ?? '',
      vitrineColor: json['vitrine_color'] ?? '#5b6af0',
      horairesJson: json['horaires_json'] ?? '{}',
    );
  }

  BusinessProfile copyWith({
    String? nom,
    String? planAbonnement,
    bool? isActive,
    String? prompt,
    String? msgConfirm,
    String? vitrineColor,
    String? horairesJson,
  }) {
    return BusinessProfile(
      id: id,
      nom: nom ?? this.nom,
      planAbonnement: planAbonnement ?? this.planAbonnement,
      isActive: isActive ?? this.isActive,
      prompt: prompt ?? this.prompt,
      msgConfirm: msgConfirm ?? this.msgConfirm,
      vitrineColor: vitrineColor ?? this.vitrineColor,
      horairesJson: horairesJson ?? this.horairesJson,
    );
  }
}
