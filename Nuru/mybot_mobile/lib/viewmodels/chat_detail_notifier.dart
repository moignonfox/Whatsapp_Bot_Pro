import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/message.dart';
import '../repositories/chat_repository.dart';
import '../core/api/socket_client.dart';
import 'chat_notifier.dart';

class ChatDetailState {
  final bool isLoading;
  final String? error;
  final List<Message> messages;
  final bool isHumanMode;

  ChatDetailState({
    required this.isLoading,
    this.error,
    required this.messages,
    required this.isHumanMode,
  });

  bool get isWithin24hWindow {
    if (messages.isEmpty) return false;
    try {
      final lastUserMsg = messages.lastWhere((m) => m.isFromUser);
      final msgDate = DateTime.parse(lastUserMsg.timestamp).toLocal();
      return DateTime.now().difference(msgDate).inHours < 24;
    } catch (e) {
      return false;
    }
  }

  ChatDetailState copyWith({
    bool? isLoading,
    String? error,
    List<Message>? messages,
    bool? isHumanMode,
  }) {
    return ChatDetailState(
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
      messages: messages ?? this.messages,
      isHumanMode: isHumanMode ?? this.isHumanMode,
    );
  }
}

class ChatDetailNotifier extends Notifier<Map<String, ChatDetailState>> {
  StreamSubscription? _msgSub;
  StreamSubscription? _humanModeSub;
  StreamSubscription? _statusSub;
  bool _isListening = false;

  @override
  Map<String, ChatDetailState> build() {
    ref.onDispose(() {
      _msgSub?.cancel();
      _humanModeSub?.cancel();
      _statusSub?.cancel();
    });
    return {};
  }

  void _initListeners() {
    if (_isListening) return;
    _isListening = true;
    
    final socketClient = ref.read(socketClientProvider);
    debugPrint('🚀 ChatDetailNotifier: Initialisation des listeners Stream !');
    
    _msgSub?.cancel();
    _msgSub = socketClient.onNewMessage.listen((data) {
      debugPrint('👉 ChatDetailNotifier onNewMessage triggered with data: $data');
      try {
        final waId = data['wa_id']?.toString();
        if (waId != null && state.containsKey(waId)) {
          final message = Message.fromSocket(data);
          final currentState = state[waId]!;
          if (!currentState.messages.any((m) => m.id == message.id)) {
            state = {
              ...state,
              waId: currentState.copyWith(
                messages: [...currentState.messages, message],
              ),
            };
            debugPrint('✅ Interface mise à jour !');
          }
        }
      } catch (e) {
        debugPrint('❌ Erreur: $e');
      }
    });

    _humanModeSub?.cancel();
    _humanModeSub = socketClient.onHumanModeToggled.listen((data) {
      final waId = data['wa_id']?.toString();
      final isHumanMode = data['state'] as bool?;
      if (waId != null && isHumanMode != null && state.containsKey(waId)) {
        final currentState = state[waId]!;
        state = {
          ...state,
          waId: currentState.copyWith(isHumanMode: isHumanMode),
        };
      }
    });

    _statusSub?.cancel();
    _statusSub = socketClient.onStatusMessage.listen((data) {
      final waId = data['wa_id']?.toString();
      final messageId = data['message_id']?.toString();
      final newStatus = data['status']?.toString();
      final mediaUrl = data['media_url']?.toString();

      if (waId != null && messageId != null && state.containsKey(waId)) {
        final currentState = state[waId]!;
        final messages = currentState.messages.map((m) {
          if (m.id == messageId || (m.messageStatus == 'processing' && mediaUrl != null && newStatus == 'sent')) {
            // Found the message, update it!
            return Message(
              id: m.id,
              role: m.role,
              content: m.content,
              timestamp: m.timestamp,
              messageType: m.messageType,
              messageStatus: newStatus ?? m.messageStatus,
              mediaUrl: mediaUrl ?? m.mediaUrl,
            );
          }
          return m;
        }).toList();

        state = {
          ...state,
          waId: currentState.copyWith(messages: messages),
        };
      }
    });
  }

  Future<void> fetchMessages(String waId) async {
    _initListeners(); // <--- GARANTI L'INITIALISATION DES LISTENERS

    final currentState = state[waId] ?? ChatDetailState(isLoading: true, messages: [], isHumanMode: false);
    state = {
      ...state,
      waId: currentState.copyWith(isLoading: true, error: null),
    };

    try {
      final repo = ref.read(chatRepositoryProvider);
      final data = await repo.getMessages(waId);
      ref.read(chatNotifierProvider.notifier).markConversationAsReadLocally(waId);
      
      state = {
        ...state,
        waId: currentState.copyWith(
          isLoading: false,
          messages: data['messages'] as List<Message>,
          isHumanMode: data['is_human_mode'] as bool,
        ),
      };
    } catch (e) {
      state = {
        ...state,
        waId: currentState.copyWith(isLoading: false, error: e.toString()),
      };
    }
  }

  Future<void> sendMessage(String waId, String text) async {
    if (text.trim().isEmpty) return;
    try {
      final repo = ref.read(chatRepositoryProvider);
      await repo.sendMessage(waId, text.trim());
      // The socket will receive the message and add it instantly, no need to reload
    } catch (e) {
      // Ignorer
    }
  }

  Future<void> uploadMedia(String waId, String filePath, String mediaType) async {
    final currentState = state[waId];
    if (currentState == null) return;
    try {
      final repo = ref.read(chatRepositoryProvider);
      // Let the UI know it's processing via optimistic UI is handled by socket `nouveau_message` with processing status!
      // But we can also do it locally if we want. For now, calling the repo will trigger the socket.
      await repo.uploadMedia(waId, filePath, mediaType);
    } catch (e) {
      debugPrint('Error uploading media: $e');
    }
  }

  Future<void> toggleHumanMode(String waId, bool activate) async {
    final currentState = state[waId];
    if (currentState == null) return;
    try {
      final repo = ref.read(chatRepositoryProvider);
      final success = await repo.toggleHumanMode(waId, activate);
      if (success) {
        state = {
          ...state,
          waId: currentState.copyWith(isHumanMode: activate),
        };
      }
    } catch (e) {}
  }
}

final chatDetailNotifierProvider = NotifierProvider<ChatDetailNotifier, Map<String, ChatDetailState>>(() {
  return ChatDetailNotifier();
});

