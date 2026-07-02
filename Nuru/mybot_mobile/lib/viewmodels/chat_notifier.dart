import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:audioplayers/audioplayers.dart';
import '../models/conversation.dart';
import '../repositories/chat_repository.dart';
import '../core/api/socket_client.dart';

final chatNotifierProvider = AsyncNotifierProvider<ChatNotifier, List<Conversation>>(ChatNotifier.new);

class ChatNotifier extends AsyncNotifier<List<Conversation>> {
  StreamSubscription? _msgSub;
  final AudioPlayer _audioPlayer = AudioPlayer();

  @override
  FutureOr<List<Conversation>> build() async {
    final socketClient = ref.watch(socketClientProvider);

    _msgSub?.cancel();
    _msgSub = socketClient.onNewMessage.listen((data) async {
      // Un nouveau message est arrivé, on recharge la liste silencieusement
      final newConversations = await _fetchConversations();
      state = AsyncValue.data(newConversations);
      
      // Jouer un son si le message vient du client
      final role = data['role']?.toString();
      if (role == 'user') {
        _playNotificationSound();
      }
    });

    ref.onDispose(() {
      _msgSub?.cancel();
      _audioPlayer.dispose();
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
