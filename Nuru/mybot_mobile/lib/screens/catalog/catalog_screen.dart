import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../viewmodels/catalog_notifier.dart';
import '../../models/product.dart';
import '../../core/api/api_client.dart';

class CatalogScreen extends ConsumerWidget {
  const CatalogScreen({super.key});

  String _buildImageUrl(String? path) {
    if (path == null || path.isEmpty) return '';
    if (path.startsWith('http')) return path;
    final baseUrl = apiClient.options.baseUrl.replaceAll('/api/v1', '');
    return '$baseUrl$path';
  }

  void _showProductForm(BuildContext context, WidgetRef ref, {Product? product}) {
    final state = ref.read(catalogNotifierProvider);
    final existingCategories = state.value?.map((p) => p.categorie).toSet().toList() ?? ['Général'];
    
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _ProductBottomSheetContent(
        isEditing: product != null,
        product: product,
        existingCategories: existingCategories,
        onSave: (data, imagePath) {
          if (product != null) {
            ref.read(catalogNotifierProvider.notifier).updateProduct(product.id, data, imagePath: imagePath);
          } else {
            ref.read(catalogNotifierProvider.notifier).addProduct(data, imagePath: imagePath);
          }
        },
      ),
    );
  }

  void _confirmDelete(BuildContext context, WidgetRef ref, Product product) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Supprimer'),
        content: Text('Voulez-vous vraiment supprimer ${product.nom} ?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Annuler'),
          ),
          TextButton(
            onPressed: () {
              ref.read(catalogNotifierProvider.notifier).deleteProduct(product.id);
              Navigator.pop(context);
            },
            child: Text('Supprimer', style: TextStyle(color: Colors.red)),
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(catalogNotifierProvider);

    return Scaffold(
      
      appBar: AppBar(
        title: const Text('Catalogue & Stocks', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        centerTitle: true,
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: Theme.of(context).colorScheme.primary,
        onPressed: () => _showProductForm(context, ref),
        child: Icon(Icons.add, color: Colors.white),
      ),
      body: state.when(
        loading: () => Center(child: CircularProgressIndicator(color: Theme.of(context).colorScheme.primary)),
        error: (error, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Erreur: $error', textAlign: TextAlign.center, style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.read(catalogNotifierProvider.notifier).fetchProducts(),
                style: ElevatedButton.styleFrom(backgroundColor: Theme.of(context).colorScheme.primary),
                child: Text('Réessayer', style: TextStyle(color: Colors.white)),
              )
            ],
          ),
        ),
        data: (products) {
          if (products.isEmpty) {
            return Center(child: Text('Aucun produit dans le catalogue.', style: TextStyle(color: Colors.grey)));
          }

          // Grouper les produits par catégorie
          final Map<String, List<Product>> groupedProducts = {};
          for (var p in products) {
            groupedProducts.putIfAbsent(p.categorie, () => []).add(p);
          }

          return ListView.builder(
              padding: const EdgeInsets.only(bottom: 80),
              itemCount: groupedProducts.keys.length,
              itemBuilder: (context, index) {
                final category = groupedProducts.keys.elementAt(index);
                final categoryProducts = groupedProducts[category]!;

                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                      child: Text(
                        category,
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black87,
                        ),
                      ),
                    ),
                    SizedBox(
                      height: 270, // Ajusté pour un meilleur rendu sans espace vide
                      child: ListView.builder(
                        scrollDirection: Axis.horizontal,
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        itemCount: categoryProducts.length,
                        itemBuilder: (context, idx) {
                          final product = categoryProducts[idx];
                          final fullImageUrl = _buildImageUrl(product.imageUrl);

                          return SizedBox(
                            width: 170, // Largeur fixe de la carte
                            child: Container(
                              margin: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
                                decoration: BoxDecoration(
                                  color: Theme.of(context).cardColor,
                                  borderRadius: BorderRadius.circular(16),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withValues(alpha: Theme.of(context).brightness == Brightness.dark ? 0.3 : 0.08),
                                      blurRadius: 16,
                                      offset: const Offset(0, 4),
                                    )
                                  ],
                                ),
                              clipBehavior: Clip.antiAlias,
                              child: Stack(
                                children: [
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.stretch,
                                    children: [
                                      // Image Header
                                      Expanded(
                                        child: fullImageUrl.isNotEmpty
                                            ? CachedNetworkImage(
                                                imageUrl: fullImageUrl,
                                                fit: BoxFit.cover,
                                                placeholder: (context, url) => _buildPlaceholder(context),
                                                errorWidget: (context, url, error) => _buildPlaceholder(context),
                                              )
                                            : _buildPlaceholder(context),
                                      ),
                                      // Content
                                      Padding(
                                        padding: const EdgeInsets.all(10.0),
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Text(
                                              product.nom,
                                              style: TextStyle(
                                                fontWeight: FontWeight.bold,
                                                fontSize: 14,
                                                decoration: product.disponible ? null : TextDecoration.lineThrough,
                                                color: product.disponible ? ((Theme.of(context).brightness == Brightness.dark) ? Colors.white : Colors.black87) : Colors.grey,
                                              ),
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                            const SizedBox(height: 2),
                                            Row(
                                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                              children: [
                                                Text(
                                                  '${product.prix.toStringAsFixed(2)} F',
                                                  style: TextStyle(
                                                    color: product.disponible ? Theme.of(context).colorScheme.secondary : Colors.grey,
                                                    fontWeight: FontWeight.w600,
                                                  ),
                                                ),
                                                Row(
                                                  children: [
                                                    Icon(Icons.timer, size: 12, color: Colors.grey),
                                                    const SizedBox(width: 2),
                                                    Text(
                                                      '${product.dureeMinutes}m',
                                                      style: const TextStyle(fontSize: 11, color: Colors.grey),
                                                    ),
                                                  ],
                                                ),
                                              ],
                                            ),
                                            const SizedBox(height: 8),
                                            // Toggles
                                            Row(
                                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                              children: [
                                                Text('Dispo', style: TextStyle(fontSize: 12, color: (Theme.of(context).brightness == Brightness.dark) ? Colors.white54 : Colors.black54)),
                                                SizedBox(
                                                  height: 26,
                                                  child: Transform.scale(
                                                    scale: 0.65,
                                                    child: Switch(
                                                      value: product.disponible,
                                                      activeColor: Theme.of(context).colorScheme.primary,
                                                      onChanged: (val) {
                                                        ref.read(catalogNotifierProvider.notifier).toggleStock(product.id);
                                                      },
                                                    ),
                                                  ),
                                                ),
                                              ],
                                            ),
                                            Row(
                                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                              children: [
                                                Text('Vitrine', style: TextStyle(fontSize: 12, color: (Theme.of(context).brightness == Brightness.dark) ? Colors.white54 : Colors.black54)),
                                                SizedBox(
                                                  height: 26,
                                                  child: Transform.scale(
                                                    scale: 0.65,
                                                    child: Switch(
                                                      value: product.isVisible,
                                                      activeColor: Theme.of(context).colorScheme.primary,
                                                      onChanged: (val) {
                                                        ref.read(catalogNotifierProvider.notifier).toggleVisibility(product.id);
                                                      },
                                                    ),
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ],
                                        ),
                                      ),
                                    ],
                                  ),
                                  // Actions Menu
                                  Positioned(
                                    top: 4,
                                    right: 4,
                                    child: Container(
                                      decoration: BoxDecoration(
                                        color: (Theme.of(context).brightness == Brightness.dark) ? Colors.black.withAlpha(150) : Colors.white.withAlpha(220),
                                        shape: BoxShape.circle,
                                      ),
                                      child: PopupMenuButton<String>(
                                        icon: Icon(Icons.more_vert, size: 20, color: Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black87),
                                        padding: EdgeInsets.zero,
                                        onSelected: (value) {
                                          if (value == 'edit') {
                                            _showProductForm(context, ref, product: product);
                                          } else if (value == 'delete') {
                                            _confirmDelete(context, ref, product);
                                          }
                                        },
                                        itemBuilder: (context) => [
                                          const PopupMenuItem(
                                            value: 'edit',
                                            child: Text('Modifier'),
                                          ),
                                          const PopupMenuItem(
                                            value: 'delete',
                                            child: Text('Supprimer', style: TextStyle(color: Colors.red)),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                );
              },
            );
        },
      ),
    );
  }

  Widget _buildPlaceholder(BuildContext context) {
    return Container(
      color: (Theme.of(context).brightness == Brightness.dark) ? const Color(0xFF334155) : Colors.grey.shade100,
      child: Center(
        child: Icon(Icons.fastfood, size: 40, color: Colors.grey),
      ),
    );
  }
}

class _ProductBottomSheetContent extends StatefulWidget {
  final bool isEditing;
  final Product? product;
  final List<String> existingCategories;
  final Function(Map<String, dynamic> data, String? imagePath) onSave;

  const _ProductBottomSheetContent({
    required this.isEditing,
    this.product,
    required this.existingCategories,
    required this.onSave,
  });

  @override
  State<_ProductBottomSheetContent> createState() => _ProductBottomSheetContentState();
}

class _ProductBottomSheetContentState extends State<_ProductBottomSheetContent> {
  late TextEditingController _nomController;
  late TextEditingController _catController;
  late TextEditingController _prixController;
  late TextEditingController _descController;
  late TextEditingController _dureeController;
  bool _isVisible = true;
  String? _selectedImagePath;

  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _nomController = TextEditingController(text: widget.product?.nom ?? '');
    _catController = TextEditingController(text: widget.product?.categorie ?? 'Général');
    
    String prixText = '';
    if (widget.product != null) {
      prixText = widget.product!.prix == widget.product!.prix.toInt() 
          ? widget.product!.prix.toInt().toString() 
          : widget.product!.prix.toString();
    }
    _prixController = TextEditingController(text: prixText);
    _descController = TextEditingController(text: widget.product?.description ?? '');
    _dureeController = TextEditingController(text: widget.product?.dureeMinutes.toString() ?? '30');
    _isVisible = widget.product?.isVisible ?? true;
  }

  @override
  void dispose() {
    _nomController.dispose();
    _catController.dispose();
    _prixController.dispose();
    _descController.dispose();
    _dureeController.dispose();
    super.dispose();
  }

  Future<void> _pickImage() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery, imageQuality: 70);
    if (image != null) {
      setState(() {
        _selectedImagePath = image.path;
      });
    }
  }

  InputDecoration _inputDecoration(String label) {
    return InputDecoration(
      labelText: label,
      labelStyle: const TextStyle(color: Colors.grey),
      filled: true,
      fillColor: Theme.of(context).brightness == Brightness.dark ? const Color(0xFF0F172A) : Colors.grey.shade50,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Theme.of(context).dividerColor)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Theme.of(context).dividerColor)),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: Theme.of(context).colorScheme.primary)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.only(topLeft: Radius.circular(20), topRight: Radius.circular(20)),
      ),
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 12,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(color: Theme.of(context).dividerColor, borderRadius: BorderRadius.circular(10)),
              ),
            ),
            Text(
              widget.isEditing ? 'Modifier le produit' : 'Nouveau produit',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black87),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            // Image Picker
            GestureDetector(
              onTap: _pickImage,
              child: Container(
                height: 140,
                decoration: BoxDecoration(
                  color: (Theme.of(context).brightness == Brightness.dark) ? const Color(0xFF334155) : Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Theme.of(context).dividerColor, style: BorderStyle.solid),
                ),
                child: _selectedImagePath != null
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(16),
                        child: Image.file(File(_selectedImagePath!), fit: BoxFit.cover),
                      )
                    : (widget.product?.imageUrl != null && widget.product!.imageUrl!.isNotEmpty)
                        ? ClipRRect(
                            borderRadius: BorderRadius.circular(16),
                            child: CachedNetworkImage(
                              imageUrl: '${apiClient.options.baseUrl.replaceAll('/api/v1', '')}${widget.product!.imageUrl!}',
                              fit: BoxFit.cover,
                              placeholder: (context, url) => Center(child: CircularProgressIndicator()),
                              errorWidget: (context, url, error) => Icon(Icons.broken_image),
                            ),
                          )
                        : Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.add_a_photo, size: 40, color: Colors.grey),
                              SizedBox(height: 8),
                              Text('Ajouter une photo', style: TextStyle(color: Colors.grey, fontWeight: FontWeight.w500)),
                            ],
                          ),
              ),
            ),
            const SizedBox(height: 20),
            TextField(
              controller: _nomController,
              decoration: _inputDecoration('Nom du produit'),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _catController,
                    decoration: _inputDecoration('Catégorie'),
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  decoration: BoxDecoration(color: (Theme.of(context).brightness == Brightness.dark) ? const Color(0xFF334155) : Colors.grey.shade100, borderRadius: BorderRadius.circular(12)),
                  child: PopupMenuButton<String>(
                    icon: Icon(Icons.arrow_drop_down, color: Theme.of(context).textTheme.bodyLarge?.color),
                    tooltip: 'Choisir une catégorie existante',
                    onSelected: (val) => setState(() => _catController.text = val),
                    itemBuilder: (context) => widget.existingCategories.map((c) => PopupMenuItem(value: c, child: Text(c))).toList(),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _prixController,
                    decoration: _inputDecoration('Prix (F)'),
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _dureeController,
                    decoration: _inputDecoration('Cuisson (min)'),
                    keyboardType: TextInputType.number,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _descController,
              decoration: _inputDecoration('Description'),
              maxLines: 3,
            ),
            const SizedBox(height: 16),
            Container(
              decoration: BoxDecoration(
                color: Theme.of(context).brightness == Brightness.dark ? const Color(0xFF0F172A) : Colors.grey.shade50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Theme.of(context).dividerColor),
              ),
              child: SwitchListTile(
                title: Text('Afficher en Vitrine', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
                activeColor: Theme.of(context).colorScheme.primary,
                value: _isVisible,
                onChanged: (val) => setState(() => _isVisible = val),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => Navigator.pop(context),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      side: BorderSide(color: Colors.grey.shade300),
                    ),
                    child: Text('Annuler', style: TextStyle(color: Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black87, fontWeight: FontWeight.bold)),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {
                      final double parsedPrix = double.tryParse(_prixController.text.replaceAll(',', '.')) ?? 0;
                      final data = {
                        'nom': _nomController.text,
                        'categorie': _catController.text,
                        'prix': parsedPrix.toInt(),
                        'duree_minutes': int.tryParse(_dureeController.text) ?? 30,
                        'description': _descController.text,
                        'is_visible': _isVisible ? 1 : 0,
                      };
                      if (_selectedImagePath == null && widget.isEditing && widget.product!.imageUrl != null) {
                        data['image_url'] = widget.product!.imageUrl!;
                      }
                      widget.onSave(data, _selectedImagePath);
                      Navigator.pop(context);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.primary,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      elevation: 0,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: Text('Sauvegarder', style: TextStyle(color: Theme.of(context).cardColor, fontWeight: FontWeight.bold)),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

