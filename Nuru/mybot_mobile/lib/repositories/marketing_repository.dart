import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api/api_client.dart';

final marketingRepositoryProvider = Provider((ref) {
  return MarketingRepository(apiClient);
});

class MarketingRepository {
  final Dio _dio;
  
  MarketingRepository(this._dio);

  Future<Map<String, dynamic>> sendCampaign({
    String? message,
    String? templateName,
    List<String>? variables,
    String? headerImageLink,
    required String target,
  }) async {
    try {
      final response = await _dio.post('/marketing/send-campaign', data: {
        if (message != null) 'message': message,
        if (templateName != null) 'template_name': templateName,
        if (variables != null) 'variables': variables,
        if (headerImageLink != null) 'header_image_link': headerImageLink,
        'target': target,
      });
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data != null) {
        throw Exception(e.response?.data['error'] ?? 'Erreur inconnue lors de l\'envoi de la campagne.');
      }
      throw Exception('Erreur de connexion : ${e.message}');
    } catch (e) {
      throw Exception('Erreur : $e');
    }
  }

  Future<int> estimateCampaign({required String target}) async {
    try {
      final response = await _dio.post('/marketing/estimate', data: {
        'target': target,
      });
      return response.data['count'] as int;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data != null) {
        throw Exception(e.response?.data['error'] ?? 'Impossible d\'estimer la campagne.');
      }
      throw Exception('Erreur de connexion : ${e.message}');
    } catch (e) {
      throw Exception('Erreur : $e');
    }
  }

  Future<String> uploadCampaignImage(String imagePath) async {
    try {
      final requestData = FormData();
      requestData.files.add(MapEntry(
        'image',
        await MultipartFile.fromFile(imagePath),
      ));
      final response = await _dio.post('/marketing/upload-image', data: requestData);
      return response.data['image_url'] as String;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data != null) {
        throw Exception(e.response?.data['error'] ?? 'Erreur lors du téléchargement de l\'image.');
      }
      throw Exception('Erreur de connexion : ${e.message}');
    } catch (e) {
      throw Exception('Erreur : $e');
    }
  }

  /// Envoie le message à Gemini via le backend et retourne la version améliorée.
  Future<String> improveMessageWithAI({required String message}) async {
    try {
      final response = await _dio.post('/marketing/improve-ai', data: {
        'message': message,
      });
      return response.data['improved_message'] as String;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data != null) {
        throw Exception(e.response?.data['error'] ?? 'Erreur IA inconnue.');
      }
      throw Exception('Erreur de connexion : ${e.message}');
    } catch (e) {
      throw Exception('Erreur : $e');
    }
  }
}
