class Product {
  final int id;
  final String businessId;
  final String categorie;
  final String nom;
  final String description;
  final double prix;
  final bool disponible;
  final String? imageUrl;
  final bool isVisible;
  final int dureeMinutes;

  Product({
    required this.id,
    required this.businessId,
    required this.categorie,
    required this.nom,
    required this.description,
    required this.prix,
    required this.disponible,
    this.imageUrl,
    required this.isVisible,
    required this.dureeMinutes,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'] ?? 0,
      businessId: json['business_id'] ?? '',
      categorie: json['categorie'] ?? 'Général',
      nom: json['nom'] ?? '',
      description: json['description'] ?? '',
      prix: (json['prix'] ?? 0).toDouble(),
      disponible: json['disponible'] == 1 || json['disponible'] == true,
      imageUrl: json['image_url'],
      isVisible: json['is_visible'] == 1 || json['is_visible'] == true,
      dureeMinutes: json['duree_minutes'] ?? 30,
    );
  }

  Product copyWith({
    bool? disponible,
    bool? isVisible,
  }) {
    return Product(
      id: id,
      businessId: businessId,
      categorie: categorie,
      nom: nom,
      description: description,
      prix: prix,
      disponible: disponible ?? this.disponible,
      imageUrl: imageUrl,
      isVisible: isVisible ?? this.isVisible,
      dureeMinutes: dureeMinutes,
    );
  }
}

