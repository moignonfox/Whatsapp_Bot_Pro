import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:intl/intl.dart';

import '../../viewmodels/backup_notifier.dart';
import '../../repositories/backup_repository.dart';

class BackupScreen extends ConsumerWidget {
  const BackupScreen({super.key});

  String _formatDate(String? isoDate) {
    if (isoDate == null) return "Jamais";
    try {
      final date = DateTime.parse(isoDate).toLocal();
      return DateFormat('dd/MM/yyyy à HH:mm').format(date);
    } catch (_) {
      return isoDate;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final backupState = ref.watch(backupNotifierProvider);
    final notifier = ref.read(backupNotifierProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Sauvegarde Google Drive'),
        centerTitle: true,
      ),
      body: backupState.isLoading && backupState.status == null
          ? const Center(child: CircularProgressIndicator())
          : _buildContent(context, backupState, notifier, ref),
    );
  }

  Widget _buildContent(BuildContext context, BackupState state, BackupNotifier notifier, WidgetRef ref) {
    final isConnected = state.status?.isConnected ?? false;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (state.error != null)
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 24),
              color: Colors.red.shade100,
              child: Text(
                state.error!,
                style: TextStyle(color: Colors.red.shade900),
              ),
            ),

          // En-tête Google Drive
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: Padding(
              padding: const EdgeInsets.all(20.0),
              child: Column(
                children: [
                  Icon(
                    isConnected ? Icons.cloud_done : Icons.cloud_off,
                    size: 64,
                    color: isConnected ? Colors.green : Colors.grey,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    isConnected ? 'Google Drive connecté' : 'Drive non connecté',
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  if (isConnected && state.status?.googleEmail != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 8.0),
                      child: Text(state.status!.googleEmail!, style: const TextStyle(color: Colors.grey)),
                    ),
                  const SizedBox(height: 24),
                  if (!isConnected)
                    ElevatedButton.icon(
                      onPressed: state.isLoading ? null : () => notifier.connectGoogleDrive(),
                      icon: const Icon(Icons.link),
                      label: const Text('Connecter mon Google Drive'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blue.shade700,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                      ),
                    ),
                  if (isConnected) ...[
                    ListTile(
                      leading: const Icon(Icons.folder, color: Colors.blue),
                      title: const Text('Dossier'),
                      subtitle: const Text('Vira Backups'),
                    ),
                    ListTile(
                      leading: const Icon(Icons.access_time, color: Colors.orange),
                      title: const Text('Dernière sauvegarde'),
                      subtitle: Text(_formatDate(state.status?.lastBackupAt)),
                    ),
                    const Divider(),
                    ElevatedButton.icon(
                      onPressed: state.isLoading
                          ? null
                          : () async {
                              final link = await notifier.triggerManualBackup();
                              if (link != null && context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text('Sauvegarde réussie !')),
                                );
                              }
                            },
                      icon: state.isLoading
                          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.sync),
                      label: const Text('Sauvegarder maintenant'),
                    ),
                  ]
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 32),
          
          const Text(
            'Ce qui est sauvegardé :',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          _buildInfoRow(Icons.check_circle, Colors.green, 'Profil boutique'),
          _buildInfoRow(Icons.check_circle, Colors.green, 'Liste des clients'),
          _buildInfoRow(Icons.check_circle, Colors.green, 'Commandes (90 derniers jours)'),
          _buildInfoRow(Icons.check_circle, Colors.green, 'Catalogue produits'),
          _buildInfoRow(Icons.cancel, Colors.red, 'Conversations WhatsApp (Privées)'),
          _buildInfoRow(Icons.cancel, Colors.red, 'Clés API et Jetons d\'accès'),

          const SizedBox(height: 48),

          if (isConnected)
            TextButton.icon(
              onPressed: state.isLoading ? null : () => _confirmDisconnect(context, notifier),
              icon: const Icon(Icons.link_off, color: Colors.red),
              label: const Text('Déconnecter Google Drive', style: TextStyle(color: Colors.red)),
            ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, Color color, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: Row(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(width: 12),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 16))),
        ],
      ),
    );
  }

  Future<void> _confirmDisconnect(BuildContext context, BackupNotifier notifier) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Déconnecter ?'),
        content: const Text('Vos sauvegardes automatiques seront désactivées.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Annuler'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Déconnecter', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (result == true) {
      notifier.disconnectGoogleDrive();
    }
  }
}
