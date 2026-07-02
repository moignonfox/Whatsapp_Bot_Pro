import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api/api_client.dart';
import '../models/conversation.dart';
import '../models/message.dart';

final chatRepositoryProvider = Provider((ref) => ChatRepository(apiClient));

class ChatRepository {
  final Dio _dio;

  ChatRepository(this._dio);

  Future<List<Conversation>> getConversations() async {
    try {
      final response = await _dio.get('/conversations');
      if (response.data['success'] == true) {
        final data = response.data['conversations'] as List;
        return data.map((json) => Conversation.fromJson(json)).toList();
      }
      return [];
    } on DioException catch (e) {
      throw Exception('Erreur réseau / API : ${e.message} ${e.response?.data}');
    } catch (e) {
      throw Exception('Erreur de chargement des conversations: $e');
    }
  }

  Future<Map<String, dynamic>> getMessages(String waId) async {
    try {
      final response = await _dio.get('/conversations/$waId/messages');
      if (response.data['success'] == true) {
        final messagesData = response.data['messages'] as List;
        final messages = messagesData.map((json) => Message.fromJson(json)).toList();
        return {
          'messages': messages,
          'is_human_mode': response.data['is_human_mode'] ?? false,
        };
      }
      return {'messages': <Message>[], 'is_human_mode': false};
    } on DioException catch (e) {
      throw Exception('Erreur réseau / API : ${e.message} ${e.response?.data}');
    } catch (e) {
      throw Exception('Erreur de chargement des messages: $e');
    }
  }

  Future<bool> sendMessage(String waId, String text) async {
    try {
      final response = await _dio.post('/conversations/$waId/send', data: {'text': text});
      return response.data['success'] == true;
    } on DioException catch (e) {
      throw Exception('Erreur lors de l\'envoi : ${e.message}');
    }
  }

  Future<bool> toggleHumanMode(String waId, bool activate) async {
    try {
      final response = await _dio.put('/conversations/$waId/toggle-mode', data: {'activate': activate});
      return response.data['success'] == true;
    } on DioException catch (e) {
      throw Exception('Erreur mode humain : ${e.message}');
    }
  }
}

