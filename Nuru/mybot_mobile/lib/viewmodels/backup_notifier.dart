import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:app_links/app_links.dart';

import '../repositories/backup_repository.dart';

class BackupState {
  final BackupStatus? status;
  final bool isLoading;
  final String? error;

  BackupState({this.status, this.isLoading = false, this.error});

  BackupState copyWith({BackupStatus? status, bool? isLoading, String? error}) {
    return BackupState(
      status: status ?? this.status,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class BackupNotifier extends Notifier<BackupState> {
  late BackupRepository _repository;
  late AppLinks _appLinks;
  StreamSubscription<Uri>? _linkSubscription;

  @override
  BackupState build() {
    _repository = ref.watch(backupRepositoryProvider);
    _initAppLinks();
    _setupDispose();
    
    // Future microtask pour lancer la récupération initiale après le build
    Future.microtask(() => fetchStatus());
    
    return BackupState(isLoading: true);
  }

  void _initAppLinks() {
    _appLinks = AppLinks();
    
    // Écouter les liens profonds entrants (vira://backup-success)
    _linkSubscription = _appLinks.uriLinkStream.listen((uri) {
      if (uri.host == 'backup-success') {
        // Le flow Google OAuth est terminé
        fetchStatus(); // Rafraîchir le statut pour afficher "Connecté"
      }
    });
  }

  // Optionnel: Riverpod gère la destruction quand le provider est autoDispose
  // Si le provider n'est pas autoDispose, il restera en mémoire. 
  // Mais on peut utiliser ref.onDispose
  
  void _setupDispose() {
    ref.onDispose(() {
      _linkSubscription?.cancel();
    });
  }

  Future<void> fetchStatus() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final status = await _repository.getBackupStatus();
      state = state.copyWith(status: status, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> connectGoogleDrive() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final url = await _repository.getGoogleAuthUrl();
      if (await canLaunchUrl(Uri.parse(url))) {
        await launchUrl(
          Uri.parse(url),
          mode: LaunchMode.externalApplication, // Forcer navigateur externe pour OAuth
        );
      } else {
        throw Exception("Impossible d'ouvrir le navigateur");
      }
      state = state.copyWith(isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> disconnectGoogleDrive() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      await _repository.disconnectDrive();
      await fetchStatus();
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<String?> triggerManualBackup() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final link = await _repository.triggerBackup();
      await fetchStatus(); // Mettre à jour "last_backup_at"
      return link;
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
      return null;
    }
  }
}

final backupNotifierProvider = NotifierProvider<BackupNotifier, BackupState>(() {
  return BackupNotifier();
});
