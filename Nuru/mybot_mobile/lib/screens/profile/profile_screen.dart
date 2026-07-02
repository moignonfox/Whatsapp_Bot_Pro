import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../viewmodels/auth_notifier.dart';
import '../../viewmodels/profile_notifier.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileState = ref.watch(profileNotifierProvider);
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Réglages', style: TextStyle(fontWeight: FontWeight.bold)),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
        children: [
          // Profile Header Section
          profileState.when(
            data: (profile) {
              if (profile == null) return const SizedBox();
              return Column(
                children: [
                  CircleAvatar(
                    radius: 40,
                    backgroundColor: colorScheme.primary.withValues(alpha: 0.1),
                    child: Text(
                    profile.nom.isNotEmpty ? profile.nom.substring(0, 1).toUpperCase() : '?',
                      style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: colorScheme.primary),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    profile.nom.isNotEmpty ? profile.nom : 'Utilisateur',
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  Text(
                    profile.email.isNotEmpty ? profile.email : 'Email non configuré',
                    style: const TextStyle(fontSize: 14, color: Colors.grey),
                  ),
                ],
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (_, __) => const SizedBox(),
          ),

          const SizedBox(height: 32),

          // Menu List
          _buildMenuCard(
            context: context,
            children: [
              _buildMenuItem(
                context: context,
                icon: Icons.person_outline,
                title: 'Profil',
                subtitle: 'Vos informations personnelles',
                onTap: () => context.go('/profile/personal'),
              ),
              _buildDivider(),
              _buildMenuItem(
                context: context,
                icon: Icons.storefront_outlined,
                title: 'Business',
                subtitle: 'Boutique, horaires, prompt IA',
                onTap: () => context.go('/profile/business'),
              ),
            ],
          ),

          const SizedBox(height: 20),

          _buildMenuCard(
            context: context,
            children: [
              _buildMenuItem(
                context: context,
                icon: Icons.lock_outline,
                title: 'Sécurité',
                subtitle: 'Mot de passe, double authentification',
                onTap: () => context.go('/profile/security'),
              ),
              _buildDivider(),
              _buildMenuItem(
                context: context,
                icon: Icons.star_border,
                title: 'Abonnement & Paiements',
                subtitle: 'Gérer CinetPay, PayGate, statut Pro',
                onTap: () => context.go('/profile/subscription'),
              ),
              _buildDivider(),
              _buildMenuItem(
                context: context,
                icon: Icons.palette_outlined,
                title: 'Affichage',
                subtitle: 'Mode clair / sombre',
                onTap: () => context.go('/profile/display'),
              ),
            ],
          ),

          const SizedBox(height: 32),

          // Logout Button
          ElevatedButton.icon(
            onPressed: () => _handleLogout(context, ref),
            icon: const Icon(Icons.logout),
            label: const Text('Se déconnecter', style: TextStyle(fontWeight: FontWeight.bold)),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red.withValues(alpha: 0.1),
              foregroundColor: Colors.red,
              elevation: 0,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
          
          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _buildMenuCard({required BuildContext context, required List<Widget> children}) {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant.withValues(alpha: 0.5)),
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(16),
        clipBehavior: Clip.antiAlias,
        child: Column(children: children),
      ),
    );
  }

  Widget _buildDivider() {
    return const Divider(height: 1, indent: 56, endIndent: 16);
  }

  Widget _buildMenuItem({
    required BuildContext context,
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return ListTile(
      onTap: onTap,
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, color: Theme.of(context).colorScheme.primary, size: 20),
      ),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 12, color: Colors.grey)),
      trailing: const Icon(Icons.chevron_right, color: Colors.grey, size: 20),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
    );
  }

  void _handleLogout(BuildContext context, WidgetRef ref) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Déconnexion'),
        content: const Text('Voulez-vous vraiment vous déconnecter ?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Annuler')),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Se déconnecter'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      await ref.read(authNotifierProvider.notifier).logout();
    }
  }
}
