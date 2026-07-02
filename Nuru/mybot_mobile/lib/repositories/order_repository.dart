import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api/api_client.dart';
import '../models/order.dart';

final orderRepositoryProvider = Provider((ref) => OrderRepository(apiClient));

class OrderRepository {
  final Dio _dio;

  OrderRepository(this._dio);

  Future<List<Order>> getOrders({String period = 'today'}) async {
    try {
      final response = await _dio.get('/orders', queryParameters: {'period': period});
      if (response.data['success'] == true) {
        final data = response.data['orders'] as List;
        return data.map((json) => Order.fromJson(json)).toList();
      }
      return [];
    } on DioException catch (e) {
      throw Exception('Erreur réseau / API : ${e.message} ${e.response?.data}');
    } catch (e) {
      throw Exception('Erreur de chargement des commandes: $e');
    }
  }

  Future<bool> updateOrderStatus(int orderId, String status) async {
    try {
      final response = await _dio.put('/orders/$orderId/status', data: {'status': status});
      return response.data['success'] == true;
    } on DioException catch (e) {
      throw Exception('Erreur de mise à jour : ${e.message} ${e.response?.data}');
    } catch (e) {
      throw Exception('Erreur: $e');
    }
  }
}

