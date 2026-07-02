import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api/api_client.dart';
import '../models/daily_stats.dart';

final statsRepositoryProvider = Provider((ref) => StatsRepository(apiClient));

class StatsRepository {
  final Dio _dio;

  StatsRepository(this._dio);

  Future<DailyStats> getTodayStats({String period = 'today'}) async {
    try {
      final response = await _dio.get('/stats/today', queryParameters: {'period': period});
      if (response.data['success'] == true) {
        return DailyStats.fromJson(response.data);
      }
      throw Exception('Erreur API inconnue');
    } on DioException catch (e) {
      throw Exception('Erreur réseau / API : ${e.message} ${e.response?.data}');
    } catch (e) {
      throw Exception('Erreur de chargement des statistiques: $e');
    }
  }
}

