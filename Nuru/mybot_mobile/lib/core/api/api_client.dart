import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// URL de l'API backend, injectée à la compilation via --dart-define=BASE_URL=...
/// Ex: flutter run --dart-define=BASE_URL=https://tidal-unseen-abrasive.ngrok-free.dev
/// En production, remplacer par l'URL définitive du serveur.
const String _baseUrl = String.fromEnvironment(
  'BASE_URL',
  defaultValue: 'https://tidal-unseen-abrasive.ngrok-free.dev',
);

class ApiClient {
  static void Function(String message, bool isSuspended)? onUnauthorized;
  final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiClient() : _dio = Dio(BaseOptions(
    baseUrl: '$_baseUrl/api/v1',
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 15),
    headers: {
      'ngrok-skip-browser-warning': 'true',
      'Accept': 'application/json',
    },
  )) {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'jwt_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onResponse: (response, handler) {
        return handler.next(response);
      },
      onError: (DioException e, handler) async {
        // Cas 1 : Compte bloqué / inactif (403)
        if (e.response?.statusCode == 403) {
          final msg = (e.response?.data is Map) ? e.response?.data['error'] : 'Votre compte a été suspendu.';
          await _storage.delete(key: 'jwt_token');
          await _storage.delete(key: 'refresh_token');
          if (onUnauthorized != null) onUnauthorized!(msg?.toString() ?? 'Votre compte a été suspendu.', true);
          return handler.next(e);
        }

        // Cas 2 : Token expiré (401)
        if (e.response?.statusCode == 401 && !e.requestOptions.path.contains('/auth/login')) {
          final refreshToken = await _storage.read(key: 'refresh_token');
          if (refreshToken != null) {
            try {
              final refreshDio = Dio(BaseOptions(
                baseUrl: '$_baseUrl/api/v1',
                headers: {
                  'ngrok-skip-browser-warning': 'true',
                  'Accept': 'application/json',
                },
              ));
              final resp = await refreshDio.post(
                '/auth/refresh',
                options: Options(headers: {'Authorization': 'Bearer $refreshToken'}),
              );
              final newAccessToken = resp.data['access_token'] as String?;
              final newRefreshToken = resp.data['refresh_token'] as String?;
              if (newAccessToken != null) {
                await _storage.write(key: 'jwt_token', value: newAccessToken);
                if (newRefreshToken != null) {
                  await _storage.write(key: 'refresh_token', value: newRefreshToken);
                }
                // Rejouer la requête originale avec le nouveau token
                e.requestOptions.headers['Authorization'] = 'Bearer $newAccessToken';
                final retryResponse = await _dio.fetch(e.requestOptions);
                return handler.resolve(retryResponse);
              }
            } catch (refreshErr) {
              await _storage.delete(key: 'jwt_token');
              await _storage.delete(key: 'refresh_token');
              if (onUnauthorized != null) onUnauthorized!('Votre session a expiré ou a été invalidée.', false);
              return handler.next(e);
            }
          } else {
            await _storage.delete(key: 'jwt_token');
            if (onUnauthorized != null) onUnauthorized!('Veuillez vous reconnecter.', false);
          }
        }
        return handler.next(e);
      },
    ));
  }

  Dio get dio => _dio;
}

final apiClient = ApiClient().dio;
