import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../api/api_client.dart';

final firebaseMessagingProvider = Provider<FirebaseMessagingService>((ref) {
  return FirebaseMessagingService();
});

class FirebaseMessagingService {
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final _storage = const FlutterSecureStorage();

  Future<void> init() async {
    // Demander les permissions sur iOS/Android
    NotificationSettings settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
    );

    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      debugPrint('✅ Permissions Firebase accordées');
    } else {
      debugPrint('❌ Permissions Firebase refusées');
      return;
    }

    // Gérer les notifications reçues pendant que l'app est en premier plan
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      debugPrint('📨 Message Firebase reçu en premier plan : ${message.notification?.title}');
      // On peut ajouter un SnackBar local ici si on le souhaite
    });

    // Envoyer le token au backend
    await _sendTokenToBackend();

    // S'assurer que le backend est informé si le token change
    _messaging.onTokenRefresh.listen((newToken) async {
      await _updateBackendWithToken(newToken);
    });
  }

  Future<void> _sendTokenToBackend() async {
    try {
      final token = await _messaging.getToken();
      if (token != null) {
        debugPrint('🔑 FCM Token généré: $token');
        await _updateBackendWithToken(token);
      }
    } catch (e) {
      debugPrint('❌ Erreur récupération FCM Token: $e');
    }
  }

  Future<void> _updateBackendWithToken(String fcmToken) async {
    try {
      final jwtToken = await _storage.read(key: 'jwt_token');
      if (jwtToken == null) return;

      final response = await apiClient.post(
        '/devices/register',
        data: {'fcm_token': fcmToken},
      );

      if (response.statusCode == 200) {
        debugPrint('✅ FCM Token envoyé au backend');
      }
    } catch (e) {
      debugPrint('❌ Erreur lors de l\'envoi du FCM Token au backend: $e');
    }
  }
}

