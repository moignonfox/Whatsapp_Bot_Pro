import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../repositories/account_repository.dart';
import 'auth_notifier.dart';
import 'package:go_router/go_router.dart';
import '../core/router.dart';
import 'package:flutter/material.dart';

final deleteAccountNotifierProvider = AsyncNotifierProvider<DeleteAccountNotifier, void>(DeleteAccountNotifier.new);

class DeleteAccountNotifier extends AsyncNotifier<void> {
  @override
  FutureOr<void> build() {}

  Future<void> deleteAccount(String password) async {
    state = const AsyncValue.loading();
    try {
      final repository = ref.read(accountRepositoryProvider);
      await repository.deleteAccount(password);
      state = const AsyncValue.data(null);
      
      // On success, show a popup and then logout
      if (rootNavigatorKey.currentContext != null) {
        final context = rootNavigatorKey.currentContext!;
        
        await showDialog(
          context: context,
          barrierDismissible: false,
          builder: (ctx) => AlertDialog(
            title: const Text('Compte supprimé', style: TextStyle(color: Colors.green)),
            content: const Text('Votre numéro WhatsApp a été libéré et vos données seront supprimées définitivement sous 30 jours.'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('OK'),
              ),
            ],
          ),
        );

        // Perform logout and it will redirect to /welcome (as per user request: "La page d'accueil")
        await ref.read(authNotifierProvider.notifier).logout();
        context.go('/welcome');
      }
    } catch (e, st) {
      state = AsyncValue.error(e, st);
      // Propager l'erreur pour pouvoir l'afficher dans l'UI si nécessaire
      rethrow;
    }
  }
}
