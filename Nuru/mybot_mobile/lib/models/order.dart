class OrderTag {
  final int id;
  final String name;
  final String color;
  final String type;

  OrderTag({
    required this.id,
    required this.name,
    required this.color,
    required this.type,
  });

  factory OrderTag.fromJson(Map<String, dynamic> json) {
    return OrderTag(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      color: json['color'] ?? '#3B82F6',
      type: json['type'] ?? 'Commande',
    );
  }
}

class Order {
  final int id;
  final String waId;
  final String clientName;
  final String details;
  final String statut;
  final String type; // 'Commande' ou 'Réservation'
  final double montant;
  final String createdAt;
  final String? dateHeureDebut;
  final List<OrderTag> tags; // Date de la réservation si c'en est une

  Order({
    required this.id,
    required this.waId,
    required this.clientName,
    required this.details,
    required this.statut,
    required this.type,
    required this.montant,
    required this.createdAt,
    this.dateHeureDebut,
    this.tags = const [],
  });

  factory Order.fromJson(Map<String, dynamic> json) {
    // Si la colonne date_heure_debut est présente et non nulle, c'est une réservation
    final String? dateDebut = json['date_heure_debut'];
    String t = json['type'] ?? json['type_commande'] ?? '';
    final String detailsText = (json['details'] ?? '').toString().toLowerCase();

    List<OrderTag> parsedTags = [];
    if (json['tags'] != null) {
      parsedTags = (json['tags'] as List).map((t) => OrderTag.fromJson(t)).toList();
    }
    

    t = 'Commande';

    return Order(
      id: json['id'] ?? 0,
      waId: json['wa_id'] ?? '',
      clientName: json['client_name'] ?? json['wa_id'] ?? 'Inconnu',
      details: json['details'] ?? '',
      statut: json['statut'] ?? 'En attente',
      type: t,
      montant: (json['montant'] ?? 0).toDouble(),
      createdAt: json['created_at'] ?? json['timestamp'] ?? '',
      dateHeureDebut: dateDebut,
      tags: parsedTags,
    );
  }

  Order copyWith({
    int? id,
    String? waId,
    String? clientName,
    String? details,
    String? statut,
    String? type,
    double? montant,
    String? createdAt,
    String? dateHeureDebut,
    List<OrderTag>? tags,
  }) {
    return Order(
      id: id ?? this.id,
      waId: waId ?? this.waId,
      clientName: clientName ?? this.clientName,
      details: details ?? this.details,
      statut: statut ?? this.statut,
      type: type ?? this.type,
      montant: montant ?? this.montant,
      createdAt: createdAt ?? this.createdAt,
      dateHeureDebut: dateHeureDebut ?? this.dateHeureDebut,
      tags: tags ?? this.tags,
    );
  }
}
