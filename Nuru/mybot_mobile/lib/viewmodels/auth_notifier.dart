import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../repositories/auth_repository.dart';
import 'profile_notifier.dart';
import 'catalog_notifier.dart';
import 'chat_notifier.dart';
import 'package:go_router/go_router.dart';
import '../core/api/api_client.dart';
import '../core/router.dart';
import 'chat_detail_notifier.dart';
import 'stats_notifier.dart';
import 'today_notifier.dart';

import 'package:flutter/material.dart';

// État de l'authentification
enum AuthStatus { unknown, authenticated, unauthenticated }

final authNotifierProvider = AsyncNotifierProvider<AuthNotifier, AuthStatus>(AuthNotifier.new);

class AuthNotifier extends AsyncNotifier<AuthStatus> {
  static bool _isDialogShowing = false;

  @override
  FutureOr<AuthStatus> build() async {
    ApiClient.onUnauthorized = (message, isSuspended) {
      state = const AsyncValue.data(AuthStatus.unauthenticated);
      final context = rootNavigatorKey.currentContext;
      
      if (context != null) {
        if (isSuspended) {
          if (!_isDialogShowing) {
            _isDialogShowing = true;
            showDialog(
              context: context,
              barrierDismissible: false,
              builder: (ctx) => AlertDialog(
                title: const Row(
                  children: [
                    Icon(Icons.lock_outline, color: Colors.red),
                    SizedBox(width: 8),
                    Text('Accès suspendu'),
                  ],
                ),
                content: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(message),
                    const SizedBox(height: 16),
                    const Text('Contactez le support Vira pour plus d\'informations.\n📧 support@vira.app'),
                  ],
                ),
                actions: [
                  TextButton(
                    onPressed: () {
                      _isDialogShowing = false;
                      Navigator.of(ctx).pop();
                      context.go('/welcome');
                    },
                    child: const Text('Compris'),
                  ),
                ],
              ),
            );
          }
        } else {
          // Expiration normale (401), on redirige sans boîte de dialogue effrayante
          context.go('/welcome');
        }
      }
    };
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

