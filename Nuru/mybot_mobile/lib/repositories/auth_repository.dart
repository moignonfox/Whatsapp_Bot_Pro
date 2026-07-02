import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';

import '../core/api/api_client.dart';

final authRepositoryProvider = Provider((ref) => AuthRepository(apiClient));

class AuthRepository {
  // ignore: unused_field
  final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  AuthRepository(this._dio);

  Future<bool> login(String email, String password) async {
    try {
      final response = await _dio.post('/auth/login', data: {
        'username': email,
        'password': password,
      });
      
      if (response.data['success'] == true) {
        final token = response.data['access_token'];
        await _storage.write(key: 'jwt_token', value: token);
        return true;
      }
      return false;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        final data = e.response?.data as Map;
        if (data.containsKey('error')) {
          throw Exception(data['error']);
        }
      }
      throw Exception('Erreur réseau : ${e.message}');
    } catch (e) {
      throw Exception('Erreur inattendue : $e');
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: 'jwt_token');
  }

  Future<String?> getToken() async {
    return await _storage.read(key: 'jwt_token');
  }
}
