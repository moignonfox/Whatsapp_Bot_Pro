import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api/api_client.dart';

final accountRepositoryProvider = Provider((ref) => AccountRepository(apiClient));

class AccountRepository {
  final Dio _dio;

  AccountRepository(this._dio);

  Future<void> deleteAccount(String password) async {
    try {
      final response = await _dio.delete(
        '/account',
        data: {'password': password},
      );
      if (response.data['success'] != true) {
        throw Exception(response.data['error'] ?? 'Erreur lors de la suppression du compte');
      }
    } on DioException catch (e) {
      throw Exception(e.response?.data['error'] ?? 'Erreur lors de la suppression du compte: ${e.message}');
    } catch (e) {
      throw Exception('Erreur: $e');
    }
  }
}
