import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:go_router/go_router.dart';
import 'package:dio/dio.dart';
import '../api/api_client.dart';
import '../router.dart';

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

    // ── Cas 1 : app en premier plan ──
    // Socket.IO gère déjà la mise à jour en temps réel dans ce cas.
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      debugPrint('📨 Message Firebase reçu en premier plan : ${message.notification?.title}');
    });

    // ── Cas 2 : app en arrière-plan, utilisateur tape sur la notification ──
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      debugPrint('🔔 Notification tapée (arrière-plan): ${message.data}');
      _scheduleNavigation(message.data['wa_id']?.toString(), delay: 0);
    });

    // ── Cas 3 : app était FERMÉE, lancée par tap sur notification (Cold Start) ──
    final initialMessage = await _messaging.getInitialMessage();
    if (initialMessage != null) {
      debugPrint('🔔 App lancée par notification: ${initialMessage.data}');
      final waId = initialMessage.data['wa_id']?.toString();
      if (waId != null && waId.isNotEmpty) {
        // Au lieu de forcer une navigation sur un router non prêt,
        // on met en file d'attente. GoRouter le lira dans son redirect() une fois auth prêt.
        pendingWaIdToNavigate = waId;
      }
    }

    // Envoyer le token FCM au backend
    await _sendTokenToBackend();

    // Renouveler le token si Firebase en génère un nouveau
    _messaging.onTokenRefresh.listen((newToken) async {
      await _updateBackendWithToken(newToken);
    });
  }

  /// Planifie la navigation vers la conversation [waId] après [delay] ms.
  /// Utilise uniquement rootNavigatorKey — aucun BuildContext async.
  void _scheduleNavigation(String? waId, {int delay = 0}) {
    if (waId == null || waId.isEmpty) return;

    void navigate() {
      final ctx = rootNavigatorKey.currentContext;
      if (ctx == null) return;
      // Navigation directe vers le détail de la conversation
      ctx.go('/chat/detail/$waId?clientName=${Uri.encodeComponent(waId)}');
    }

    if (delay <= 0) {
      navigate();
    } else {
      Future.delayed(Duration(milliseconds: delay), navigate);
    }
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
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        debugPrint("⚠️ FCM Token non envoyé : session expirée (401).");
        return;
      }
      debugPrint("❌ Erreur lors de l'envoi du FCM Token: $e");
    } catch (e) {
      debugPrint("❌ Erreur inattendue lors de l'envoi du FCM Token: $e");
    }
  }
}
