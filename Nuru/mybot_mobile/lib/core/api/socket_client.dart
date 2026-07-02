import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:socket_io_client/socket_io_client.dart' as socket_io;
import 'api_client.dart';

final socketClientProvider = Provider<SocketClient>((ref) {
  final client = SocketClient();
  ref.onDispose(() {
    client.disconnect();
  });
  return client;
});

class SocketClient {
  socket_io.Socket? _socket;
  final _storage = const FlutterSecureStorage();

  void init() async {
    if (_socket != null && _socket!.connected) return;

    final token = await _storage.read(key: 'jwt_token');
    if (token == null) return;

    // Récupère l'URL de base (sans /api/v1)
    String baseUrl = apiClient.options.baseUrl.replaceAll('/api/v1', '');
    if (baseUrl.endsWith('/')) {
      baseUrl = baseUrl.substring(0, baseUrl.length - 1);
    }

    _socket = socket_io.io(baseUrl, socket_io.OptionBuilder()
      .setTransports(['websocket'])
      .disableAutoConnect()
      .setExtraHeaders({'ngrok-skip-browser-warning': 'true'})
      .build()
    );

    _socket?.onConnect((_) {
      debugPrint('✅ Connecté au Socket.IO backend');
      _socket?.emit('authenticate_jwt', {'token': token});
    });

    _socket?.on('nouveau_message', (data) {
      debugPrint('📨 SOCKET: nouveau_message reçu: $data');
      if (data is Map) {
        try {
          final safeData = <String, dynamic>{};
          for (var k in data.keys) { safeData[k.toString()] = data[k]; }
          debugPrint('📨 Ajout au Stream onNewMessage: $safeData');
          _messageController.add(safeData);
        } catch(e) {
          debugPrint('❌ Erreur Stream nouveau_message: $e');
        }
      }
    });

    _socket?.on('nouvelle_commande', (data) {
      debugPrint('📦 SOCKET: nouvelle_commande reçue: $data');
      if (data is Map) {
        final safeData = <String, dynamic>{};
        for (var k in data.keys) { safeData[k.toString()] = data[k]; }
        _orderController.add(safeData);
      }
    });

    _socket?.on('statut_commande', (data) {
      debugPrint('🔄 SOCKET: statut_commande reçu: $data');
      if (data is Map) {
        final safeData = <String, dynamic>{};
        for (var k in data.keys) { safeData[k.toString()] = data[k]; }
        _orderStatusController.add(safeData);
      }
    });

    _socket?.on('human_mode_toggled', (data) {
      if (data is Map) {
        final safeData = <String, dynamic>{};
        for (var k in data.keys) { safeData[k.toString()] = data[k]; }
        _humanModeController.add(safeData);
      }
    });

    _socket?.onDisconnect((_) => debugPrint('❌ Déconnecté du Socket.IO'));
    
    _socket?.connect();
  }

  final _messageController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get onNewMessage => _messageController.stream;

  final _orderController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get onNewOrder => _orderController.stream;

  final _orderStatusController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get onOrderStatusChanged => _orderStatusController.stream;

  final _humanModeController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get onHumanModeToggled => _humanModeController.stream;

  void disconnect() {
    _socket?.disconnect();
    _socket?.dispose();
    _socket = null;
    _messageController.close();
    _orderController.close();
    _orderStatusController.close();
    _humanModeController.close();
  }

  void on(String event, Function(dynamic) handler) {
    _socket?.on(event, handler);
  }

  void off(String event) {
    _socket?.off(event);
  }
}

