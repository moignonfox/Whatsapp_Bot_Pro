import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/daily_stats.dart';
import '../repositories/stats_repository.dart';
import '../core/api/socket_client.dart';

class StatsPeriodNotifier extends Notifier<String> {
  @override
  String build() => 'today';

  void setPeriod(String p) {
    state = p;
  }
}

final statsPeriodProvider = NotifierProvider<StatsPeriodNotifier, String>(StatsPeriodNotifier.new);

final statsNotifierProvider = AsyncNotifierProvider<StatsNotifier, DailyStats>(StatsNotifier.new);

class StatsNotifier extends AsyncNotifier<DailyStats> {
  StreamSubscription? _orderSub;
  StreamSubscription? _statusSub;

  @override
  FutureOr<DailyStats> build() async {
    final period = ref.watch(statsPeriodProvider);
    final socketClient = ref.watch(socketClientProvider);

    _orderSub?.cancel();
    _orderSub = socketClient.onNewOrder.listen((_) {
      fetchStatsSilently();
    });

    _statusSub?.cancel();
    _statusSub = socketClient.onOrderStatusChanged.listen((_) {
      fetchStatsSilently();
    });

    ref.onDispose(() {
      _orderSub?.cancel();
      _statusSub?.cancel();
    });

    final repo = ref.read(statsRepositoryProvider);
    return repo.getTodayStats(period: period);
  }

  Future<void> fetchStatsSilently() async {
    final period = ref.read(statsPeriodProvider);
    final repo = ref.read(statsRepositoryProvider);
    final newStats = await repo.getTodayStats(period: period);
    state = AsyncValue.data(newStats);
  }

  Future<void> fetchStats() async {
    state = const AsyncValue.loading();
    final period = ref.read(statsPeriodProvider);
    final repo = ref.read(statsRepositoryProvider);
    state = await AsyncValue.guard(() => repo.getTodayStats(period: period));
  }
}

