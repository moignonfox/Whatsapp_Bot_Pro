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
  
  // Track last seen IDs for catch-up
  int _lastMessageId = 0;
  int _lastOrderId = 0;

  Future<void> _loadLastIds() async {
    final msgIdStr = await _storage.read(key: 'last_message_id');
    final ordIdStr = await _storage.read(key: 'last_order_id');
    if (msgIdStr != null) _lastMessageId = int.tryParse(msgIdStr) ?? 0;
    if (ordIdStr != null) _lastOrderId = int.tryParse(ordIdStr) ?? 0;
  }

  void _saveLastMessageId(int id) {
    if (id > _lastMessageId) {
      _lastMessageId = id;
      _storage.write(key: 'last_message_id', value: id.toString());
    }
  }

  void _saveLastOrderId(int id) {
    if (id > _lastOrderId) {
      _lastOrderId = id;
      _storage.write(key: 'last_order_id', value: id.toString());
    }
  }

  void init() async {
    if (_socket != null) return; // Prevent duplicate instantiation

    await _loadLastIds();
    final token = await _storage.read(key: 'jwt_token');
    if (token == null) return;

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

    _setupListeners(token);
    _socket?.connect();
  }

  void _setupListeners(String token) {
    _socket?.onConnect((_) {
      debugPrint('✅ Connecté au Socket.IO backend');
      _socket?.emit('authenticate_jwt', {
        'token': token,
        'last_message_id': _lastMessageId,
        'last_order_id': _lastOrderId
      });
    });

    _socket?.on('force_logout', (data) {
      debugPrint('🛑 Déconnexion forcée par le serveur via Socket');
      String reason = 'Votre compte a été suspendu par l\'administrateur.';
      if (data != null && data is Map && data['reason'] != null) {
        reason = data['reason'].toString();
      }
      if (ApiClient.onUnauthorized != null) {
        ApiClient.onUnauthorized!(reason, true);
      }
    });

    _socket?.on('nouveau_message', (data) {
      if (data is Map) {
        try {
          if (data['id'] != null) {
            _saveLastMessageId(int.tryParse(data['id'].toString()) ?? 0);
          } else if (data['message_id'] != null) {
            _saveLastMessageId(int.tryParse(data['message_id'].toString()) ?? 0);
          }

          final safeData = <String, dynamic>{};
          for (var k in data.keys) { safeData[k.toString()] = data[k]; }
          _messageController.add(safeData);
        } catch(e) {
          debugPrint('❌ Erreur Stream nouveau_message: $e');
        }
      }
    });

    _socket?.on('statut_message', (data) {
      if (data is Map) {
        try {
          final safeData = <String, dynamic>{};
          for (var k in data.keys) { safeData[k.toString()] = data[k]; }
          _statusMessageController.add(safeData);
        } catch(e) {
          debugPrint('❌ Erreur Stream statut_message: $e');
        }
      }
    });

    _socket?.on('nouvelle_commande', (data) {
      if (data is Map) {
        if (data['res_id'] != null) {
          _saveLastOrderId(int.tryParse(data['res_id'].toString()) ?? 0);
        }
        final safeData = <String, dynamic>{};
        for (var k in data.keys) { safeData[k.toString()] = data[k]; }
        _orderController.add(safeData);
      }
    });

    _socket?.on('statut_commande', (data) {
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

    // --- Rattrapage (Catch-up) ---
    _socket?.on('sync_missed_events', (data) {
      if (data is Map) {
        debugPrint('🔄 Rattrapage SocketIO reçu : $data');
        final messages = data['messages'] as List?;
        final orders = data['orders'] as List?;

        if (messages != null) {
          for (var msg in messages) {
            if (msg is Map) {
              if (msg['id'] != null) _saveLastMessageId(int.tryParse(msg['id'].toString()) ?? 0);
              
              final safeData = <String, dynamic>{};
              for (var k in msg.keys) { safeData[k.toString()] = msg[k]; }
              _messageController.add(safeData); // Réinjecte comme un event live
            }
          }
        }

        if (orders != null) {
          for (var order in orders) {
            if (order is Map) {
              if (order['id'] != null) _saveLastOrderId(int.tryParse(order['id'].toString()) ?? 0);
              
              final safeData = <String, dynamic>{};
              for (var k in order.keys) { safeData[k.toString()] = order[k]; }
              _orderController.add(safeData); // Réinjecte comme un event live
            }
          }
        }
      }
    });

    _socket?.onDisconnect((_) => debugPrint('❌ Déconnecté du Socket.IO'));
  }

  Future<void> reconnect() async {
    // Si déjà connecté, on ne fait rien
    if (_socket != null && _socket!.connected) return;

    final token = await _storage.read(key: 'jwt_token');
    if (token == null) return;

    if (_socket == null) {
      init();
    } else {
      await _loadLastIds(); // Recharge au cas où
      _socket?.connect(); // Reconnecte l'instance existante sans recréer de listeners
    }
  }

  final _messageController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get onNewMessage => _messageController.stream;

  final _statusMessageController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get onStatusMessage => _statusMessageController.stream;

  final _orderController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get onNewOrder => _orderController.stream;

  final _orderStatusController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get onOrderStatusChanged => _orderStatusController.stream;

  final _humanModeController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get onHumanModeToggled => _humanModeController.stream;

  final _accountApprovedController = StreamController<bool>.broadcast();
  Stream<bool> get onAccountApproved => _accountApprovedController.stream;

  void disconnect() {
    _socket?.disconnect();
    _socket?.dispose();
    _socket = null;
    _messageController.close();
    _statusMessageController.close();
    _orderController.close();
    _orderStatusController.close();
    _humanModeController.close();
    _accountApprovedController.close();
  }

  void on(String event, Function(dynamic) handler) {
    _socket?.on(event, handler);
  }

  void off(String event) {
    _socket?.off(event);
  }
}
