import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api/api_client.dart';
import '../models/business_profile.dart';

final profileRepositoryProvider = Provider((ref) => ProfileRepository(apiClient));

class ProfileRepository {
  final Dio _dio;

  ProfileRepository(this._dio);

  Future<BusinessProfile> getProfile() async {
    try {
      final response = await _dio.get('/auth/me');
      if (response.data['success'] == true) {
        return BusinessProfile.fromJson(response.data['company']);
      }
      throw Exception('Erreur de récupération du profil');
    } on DioException catch (e) {
      throw Exception('Erreur API Profil: ${e.message}');
    } catch (e) {
      throw Exception('Erreur: $e');
    }
  }

  Future<bool> updateProfile(Map<String, dynamic> data) async {
    try {
      final response = await _dio.put('/auth/me', data: data);
      return response.data['success'] == true;
    } on DioException catch (e) {
      throw Exception('Erreur API Update Profil: ${e.message}');
    } catch (e) {
      throw Exception('Erreur: $e');
    }
  }

  Future<bool> updatePassword(String oldPassword, String newPassword) async {
    try {
      final response = await _dio.put('/auth/password', data: {
        'old_password': oldPassword,
        'new_password': newPassword,
      });
      return response.data['success'] == true;
    } on DioException catch (e) {
      throw Exception(e.response?.data['error'] ?? 'Erreur lors du changement de mot de passe');
    } catch (e) {
      throw Exception('Erreur: $e');
    }
  }

  Future<bool> uploadImages({String? logoPath, String? coverPath}) async {
    try {
      final formData = FormData();
      if (logoPath != null) {
        formData.files.add(MapEntry('logo', await MultipartFile.fromFile(logoPath)));
      }
      if (coverPath != null) {
        formData.files.add(MapEntry('cover', await MultipartFile.fromFile(coverPath)));
      }
      final response = await _dio.post('/auth/me/images', data: formData);
      return response.data['success'] == true;
    } on DioException catch (e) {
      throw Exception(e.response?.data['error'] ?? 'Erreur lors de l\'envoi des images');
    } catch (e) {
      throw Exception('Erreur: $e');
    }
  }
}

