import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/order.dart';
import '../repositories/order_repository.dart';
import '../core/api/socket_client.dart';
import 'stats_notifier.dart';

final todayNotifierProvider = AsyncNotifierProvider<TodayNotifier, List<Order>>(TodayNotifier.new);

class TodayNotifier extends AsyncNotifier<List<Order>> {
  StreamSubscription? _orderSub;
  StreamSubscription? _statusSub;

  @override
  FutureOr<List<Order>> build() async {
    final socketClient = ref.watch(socketClientProvider);
    // Register dependency so it rebuilds when period changes
    ref.watch(statsPeriodProvider);

    _orderSub?.cancel();
    _orderSub = socketClient.onNewOrder.listen((_) async {
      // Silent update for better UX
      final newOrders = await _fetchOrders();
      state = AsyncValue.data(newOrders);
    });

    _statusSub?.cancel();
    _statusSub = socketClient.onOrderStatusChanged.listen((_) async {
      final newOrders = await _fetchOrders();
      state = AsyncValue.data(newOrders);
    });

    ref.onDispose(() {
      _orderSub?.cancel();
      _statusSub?.cancel();
    });

    return _fetchOrders();
  }

  Future<List<Order>> _fetchOrders() async {
    final period = ref.read(statsPeriodProvider);
    final repo = ref.read(orderRepositoryProvider);
    return repo.getOrders(period: period);
  }

  Future<void> fetchOrders() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => _fetchOrders());
  }

  Future<void> updateOrderStatus(int orderId, String status) async {
    try {
      // Optimistic update : on met à jour l'état localement d'abord sans charger
      if (state.hasValue) {
        final updatedOrders = state.value!.map((o) {
          if (o.id == orderId) {
            return o.copyWith(statut: status);
          }
          return o;
        }).toList();
        state = AsyncValue.data(updatedOrders);
      }

      final repo = ref.read(orderRepositoryProvider);
      final success = await repo.updateOrderStatus(orderId, status);
      
      if (!success) {
        // En cas d'erreur, on recharge les vraies données depuis le serveur
        final realOrders = await _fetchOrders();
        state = AsyncValue.data(realOrders);
      }
    } catch (e) {
      // Si exception, on revient à l'état réel
      final realOrders = await _fetchOrders();
      state = AsyncValue.data(realOrders);
      throw Exception('Erreur de mise à jour: $e');
    }
  }
}

