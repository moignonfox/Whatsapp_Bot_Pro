import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api/api_client.dart';

class BackupStatus {
  final bool isConnected;
  final String? lastBackupAt;
  final bool backupEnabled;
  final String? googleEmail;

  BackupStatus({
    required this.isConnected,
    this.lastBackupAt,
    required this.backupEnabled,
    this.googleEmail,
  });

  factory BackupStatus.fromJson(Map<String, dynamic> json) {
    return BackupStatus(
      isConnected: json['is_connected'] ?? false,
      lastBackupAt: json['last_backup_at'],
      backupEnabled: json['backup_enabled'] ?? false,
      googleEmail: json['google_email'],
    );
  }
}

class BackupRepository {
  final Dio dio;

  BackupRepository(this.dio);

  Future<String> getGoogleAuthUrl() async {
    final response = await dio.get('/backup/google/auth-url');
    if (response.data['success'] == true) {
      return response.data['auth_url'];
    }
    throw Exception(response.data['error'] ?? 'Failed to get auth url');
  }

  Future<BackupStatus> getBackupStatus() async {
    final response = await dio.get('/backup/google/status');
    if (response.data['success'] == true) {
      return BackupStatus.fromJson(response.data);
    }
    throw Exception(response.data['error'] ?? 'Failed to get status');
  }

  Future<String> triggerBackup() async {
    final response = await dio.post('/backup/google/trigger');
    if (response.data['success'] == true) {
      return response.data['drive_link'] ?? '';
    }
    throw Exception(response.data['error'] ?? 'Backup failed');
  }

  Future<void> disconnectDrive() async {
    final response = await dio.delete('/backup/google/disconnect');
    if (response.data['success'] != true) {
      throw Exception(response.data['error'] ?? 'Failed to disconnect');
    }
  }

  // L'URL de téléchargement CSV
  String getCsvExportUrl(String type) {
    return '${dio.options.baseUrl}/backup/export/csv?type=$type';
  }
}

final backupRepositoryProvider = Provider<BackupRepository>((ref) {
  return BackupRepository(apiClient);
});
