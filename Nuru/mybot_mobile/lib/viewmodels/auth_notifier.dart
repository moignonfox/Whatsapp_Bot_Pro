import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../repositories/auth_repository.dart';
import 'profile_notifier.dart';
import 'catalog_notifier.dart';
import 'chat_notifier.dart';
import 'chat_detail_notifier.dart';
import 'stats_notifier.dart';
import 'today_notifier.dart';

// État de l'authentification
enum AuthStatus { unknown, authenticated, unauthenticated }

final authNotifierProvider = AsyncNotifierProvider<AuthNotifier, AuthStatus>(AuthNotifier.new);

class AuthNotifier extends AsyncNotifier<AuthStatus> {
  @override
  FutureOr<AuthStatus> build() async {
    return _checkToken();
  }

  Future<AuthStatus> _checkToken() async {
    final repository = ref.watch(authRepositoryProvider);
    final token = await repository.getToken();
    return token != null ? AuthStatus.authenticated : AuthStatus.unauthenticated;
  }

  Future<void> login(String email, String password) async {
    state = const AsyncValue.loading();
    try {
      final repository = ref.watch(authRepositoryProvider);
      await repository.login(email, password);
      state = const AsyncValue.data(AuthStatus.authenticated);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> logout() async {
    final repository = ref.read(authRepositoryProvider);
    await repository.logout();
    
    ref.invalidate(profileNotifierProvider);
    ref.invalidate(catalogNotifierProvider);
    ref.invalidate(chatNotifierProvider);
    ref.invalidate(chatDetailNotifierProvider);
    ref.invalidate(statsNotifierProvider);
    ref.invalidate(statsPeriodProvider);
    ref.invalidate(todayNotifierProvider);
    
    state = const AsyncValue.data(AuthStatus.unauthenticated);
  }
}

