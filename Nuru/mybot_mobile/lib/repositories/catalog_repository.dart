import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api/api_client.dart';
import '../models/product.dart';

final catalogRepositoryProvider = Provider((ref) => CatalogRepository(apiClient));

class CatalogRepository {
  final Dio _dio;

  CatalogRepository(this._dio);

  Future<List<Product>> getProducts() async {
    try {
      final response = await _dio.get('/catalog/products');
      if (response.data['success'] == true) {
        final data = response.data['products'] as List;
        return data.map((json) => Product.fromJson(json)).toList();
      }
      return [];
    } on DioException catch (e) {
      throw Exception('Erreur réseau / API : ${e.message} ${e.response?.data}');
    } catch (e) {
      throw Exception('Erreur de chargement du catalogue: $e');
    }
  }

  Future<bool> toggleStock(int productId) async {
    try {
      final response = await _dio.put('/catalog/products/$productId/stock');
      return response.data['success'] == true;
    } on DioException catch (e) {
      throw Exception('Erreur de mise à jour : ${e.message} ${e.response?.data}');
    } catch (e) {
      throw Exception('Erreur: $e');
    }
  }

  Future<bool> addProduct(Map<String, dynamic> data, {String? imagePath}) async {
    try {
      final requestData = FormData.fromMap(data);
      if (imagePath != null && imagePath.isNotEmpty) {
        requestData.files.add(MapEntry(
          'image',
          await MultipartFile.fromFile(imagePath),
        ));
      }
      
      final response = await _dio.post('/catalog/products', data: requestData);
      return response.data['success'] == true;
    } on DioException catch (e) {
      throw Exception('Erreur d\'ajout : ${e.message} ${e.response?.data}');
    }
  }

  Future<bool> updateProduct(int productId, Map<String, dynamic> data, {String? imagePath}) async {
    try {
      final requestData = FormData.fromMap(data);
      if (imagePath != null && imagePath.isNotEmpty) {
        requestData.files.add(MapEntry(
          'image',
          await MultipartFile.fromFile(imagePath),
        ));
      }
      
      final response = await _dio.put('/catalog/products/$productId', data: requestData);
      return response.data['success'] == true;
    } on DioException catch (e) {
      throw Exception('Erreur de mise à jour : ${e.message} ${e.response?.data}');
    }
  }

  Future<bool> deleteProduct(int productId) async {
    try {
      final response = await _dio.delete('/catalog/products/$productId');
      return response.data['success'] == true;
    } on DioException catch (e) {
      throw Exception('Erreur de suppression : ${e.message} ${e.response?.data}');
    }
  }
}
