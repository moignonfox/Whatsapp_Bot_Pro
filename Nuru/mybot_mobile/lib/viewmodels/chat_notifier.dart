import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:audioplayers/audioplayers.dart';
import '../models/conversation.dart';
import '../repositories/chat_repository.dart';
import '../core/api/socket_client.dart';
import 'package:flutter/foundation.dart';

final chatNotifierProvider = AsyncNotifierProvider<ChatNotifier, List<Conversation>>(ChatNotifier.new);

class ChatNotifier extends AsyncNotifier<List<Conversation>> {
  StreamSubscription? _msgSub;
  final AudioPlayer _audioPlayer = AudioPlayer();

  @override
  FutureOr<List<Conversation>> build() async {
    final socketClient = ref.watch(socketClientProvider);

    _msgSub?.cancel();
    _msgSub = socketClient.onNewMessage.listen((data) async {
      // ── Mise à jour locale INSTANTANÉE ──
      // On ne fait pas d'appel HTTP — on met à jour directement l'état local
      // pour que la conversation remonte en haut immédiatement.
      final waId       = data['wa_id']?.toString() ?? '';
      final content    = data['content']?.toString() ?? '';
      final timestamp  = data['timestamp']?.toString() ?? '';
      final clientName = data['client_name']?.toString();
      final role       = data['role']?.toString() ?? '';

      if (waId.isNotEmpty && state.hasValue) {
        final current = List<Conversation>.from(state.value!);
        final idx = current.indexWhere((c) => c.id == waId);

        if (idx >= 0) {
          // Conversation existante — mettre à jour et remonter en tête
          final updated = current[idx].copyWith(
            lastMessage:   content,
            lastTimestamp: timestamp,
            clientName:    clientName ?? current[idx].clientName,
            unreadCount:   role == 'user' ? (current[idx].unreadCount + 1) : current[idx].unreadCount,
          );
          current.removeAt(idx);
          current.insert(0, updated);
        } else {
          // Nouvelle conversation inconnue — ajouter en tête
          current.insert(0, Conversation(
            id:            waId,
            clientName:    clientName ?? waId,
            lastMessage:   content,
            lastTimestamp: timestamp,
            unreadCount:   role == 'user' ? 1 : 0,
          ));
        }
        state = AsyncValue.data(current);
      }

      // Jouer le son si c'est un message client
      if (role == 'user') {
        _playNotificationSound();
      }

      // Rafraîchissement silencieux en arrière-plan pour rester en sync
      // (les données locales sont déjà à jour donc l'utilisateur ne verra pas de flash)
      Future.delayed(const Duration(milliseconds: 800), () async {
        try {
          final fresh = await _fetchConversations();
          state = AsyncValue.data(fresh);
        } catch (_) {}
      });
    });

    ref.onDispose(() {
      _msgSub?.cancel();
      _audioPlayer.dispose().catchError((e) {
        debugPrint('Ignored dispose error: $e');
      });
    });

    return _fetchConversations();
  }
  
  Future<void> _playNotificationSound() async {
    try {
      await _audioPlayer.play(AssetSource('audio/notification.wav'));
    } catch (e) {
      // Ignorer l'erreur si le son ne peut pas être joué
    }
  }

  Future<List<Conversation>> _fetchConversations() async {
    final repository = ref.watch(chatRepositoryProvider);
    return repository.getConversations();
  }

  Future<void> fetchConversations() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => _fetchConversations());
  }

  void markConversationAsReadLocally(String waId) {
    if (state.value == null) return;
    
    final updatedList = state.value!.map((conv) {
      if (conv.id == waId) {
        return conv.copyWith(unreadCount: 0);
      }
      return conv;
    }).toList();
    
    state = AsyncValue.data(updatedList);
  }
}
