import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../repositories/marketing_repository.dart';

final marketingNotifierProvider = AsyncNotifierProvider<MarketingNotifier, Map<String, dynamic>?>(MarketingNotifier.new);

class MarketingNotifier extends AsyncNotifier<Map<String, dynamic>?> {
  @override
  FutureOr<Map<String, dynamic>?> build() {
    return null;
  }

  Future<bool> sendCampaign(String message, String target) async {
    state = const AsyncValue.loading();
    try {
      final repository = ref.read(marketingRepositoryProvider);
      final result = await repository.sendCampaign(message: message, target: target);
      state = AsyncValue.data(result);
      return true;
    } catch (e, st) {
      state = AsyncValue.error(e, st);
      return false;
    }
  }
}
