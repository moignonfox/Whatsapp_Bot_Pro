import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/product.dart';
import '../repositories/catalog_repository.dart';

final catalogNotifierProvider = AsyncNotifierProvider<CatalogNotifier, List<Product>>(CatalogNotifier.new);

class CatalogNotifier extends AsyncNotifier<List<Product>> {
  @override
  FutureOr<List<Product>> build() async {
    return _fetchProducts();
  }

  Future<List<Product>> _fetchProducts() async {
    final repo = ref.watch(catalogRepositoryProvider);
    return repo.getProducts();
  }

  Future<void> fetchProducts() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => _fetchProducts());
  }

  Future<void> toggleStock(int productId) async {
    try {
      final repo = ref.read(catalogRepositoryProvider);
      
      // Optimistic UI update
      if (state.hasValue) {
        final currentProducts = state.value!;
        final newProducts = currentProducts.map((p) {
          if (p.id == productId) {
            return p.copyWith(disponible: !p.disponible);
          }
          return p;
        }).toList();
        state = AsyncValue.data(newProducts);
      }
      
      final success = await repo.toggleStock(productId);
      if (!success) {
        // Rollback on failure by refreshing
        await fetchProducts();
      }
    } catch (e) {
      // Rollback on failure
      await fetchProducts();
      throw Exception('Erreur de mise à jour: $e');
    }
  }
  Future<void> addProduct(Map<String, dynamic> data, {String? imagePath}) async {
    try {
      final repo = ref.read(catalogRepositoryProvider);
      final success = await repo.addProduct(data, imagePath: imagePath);
      if (success) {
        await fetchProducts();
      }
    } catch (e) {
      throw Exception('Erreur d\'ajout: $e');
    }
  }

  Future<void> updateProduct(int productId, Map<String, dynamic> data, {String? imagePath}) async {
    try {
      final repo = ref.read(catalogRepositoryProvider);
      final success = await repo.updateProduct(productId, data, imagePath: imagePath);
      if (success) {
        await fetchProducts();
      }
    } catch (e) {
      throw Exception('Erreur de mise à jour: $e');
    }
  }

  Future<void> deleteProduct(int productId) async {
    try {
      final repo = ref.read(catalogRepositoryProvider);
      final success = await repo.deleteProduct(productId);
      if (success) {
        await fetchProducts();
      }
    } catch (e) {
      throw Exception('Erreur de suppression: $e');
    }
  }
}
