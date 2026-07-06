import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

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
        final refreshToken = response.data['refresh_token'];
        
        await _storage.write(key: 'jwt_token', value: token);
        if (refreshToken != null) {
          await _storage.write(key: 'refresh_token', value: refreshToken);
        }
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

  /// Inscription d'un nouveau compte (connexion automatique après)
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String nom,
    required String ownerName,
    required String ownerPhone,
    required String requestedBotPhone,
    required String businessType,
    required String devise,
    required String ville,
    required List<String> botTasks,
    required String tone,
    required String businessInfo,
  }) async {
    try {
      final response = await _dio.post('/auth/register', data: {
        'email': email,
        'password': password,
        'nom': nom,
        'owner_name': ownerName,
        'owner_phone': ownerPhone,
        'requested_bot_phone': requestedBotPhone,
        'business_type': businessType,
        'devise': devise,
        'ville': ville,
        'bot_tasks': botTasks,
        'tone': tone,
        'business_info': businessInfo,
      });

      if (response.data['success'] == true) {
        final token = response.data['access_token'];
        await _storage.write(key: 'jwt_token', value: token);
        return response.data;
      }
      throw Exception(response.data['error'] ?? 'Erreur inconnue');
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        final data = e.response?.data as Map;
        if (data.containsKey('error')) {
          throw Exception(data['error']);
        }
      }
      throw Exception('Erreur réseau : ${e.message}');
    } catch (e) {
      rethrow;
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: 'jwt_token');
  }

  Future<String?> getToken() async {
    return await _storage.read(key: 'jwt_token');
  }
}
