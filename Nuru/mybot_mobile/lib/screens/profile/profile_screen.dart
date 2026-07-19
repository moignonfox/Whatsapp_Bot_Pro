import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../viewmodels/auth_notifier.dart';
import '../../viewmodels/profile_notifier.dart';
import '../../core/subscription_gate.dart';
import '../../core/feature_gate_widget.dart';
import '../../core/api/api_client.dart';

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
              final baseUrl = apiClient.options.baseUrl.replaceAll('/api/v1', '');
              
              String? coverUrl;
              if (profile.vitrineCoverUrl != null && profile.vitrineCoverUrl!.isNotEmpty) {
                coverUrl = profile.vitrineCoverUrl!.startsWith('http') 
                  ? profile.vitrineCoverUrl 
                  : '$baseUrl${profile.vitrineCoverUrl}';
              }
              
              String? logoUrl;
              if (profile.vitrineLogoUrl != null && profile.vitrineLogoUrl!.isNotEmpty) {
                logoUrl = profile.vitrineLogoUrl!.startsWith('http') 
                  ? profile.vitrineLogoUrl 
                  : '$baseUrl${profile.vitrineLogoUrl}';
              }

              return Column(
                children: [
                  Container(
                    height: 120,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      color: colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(16),
                      image: coverUrl != null
                          ? DecorationImage(
                              image: NetworkImage(coverUrl),
                              fit: BoxFit.cover,
                            )
                          : null,
                    ),
                    child: Stack(
                      clipBehavior: Clip.none,
                      alignment: Alignment.bottomCenter,
                      children: [
                        Positioned(
                          bottom: -40,
                          child: CircleAvatar(
                            radius: 44,
                            backgroundColor: Theme.of(context).scaffoldBackgroundColor,
                            child: CircleAvatar(
                              radius: 40,
                              backgroundColor: colorScheme.primary.withValues(alpha: 0.1),
                              backgroundImage: logoUrl != null ? NetworkImage(logoUrl) : null,
                              child: logoUrl == null
                                  ? Text(
                                      profile.nom.isNotEmpty ? profile.nom.substring(0, 1).toUpperCase() : '?',
                                      style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: colorScheme.primary),
                                    )
                                  : null,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 52),
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
              _buildDivider(),
              _buildMenuItem(
                context: context,
                icon: Icons.inventory_2_outlined,
                title: 'Catalogue & Stocks',
                subtitle: 'Gérer les produits et la disponibilité',
                onTap: () => context.push('/catalog'),
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

          const SizedBox(height: 20),

          // Pro & Premium Features Section
          const Text(
            ' Outils Avancés',
            style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey, fontSize: 13),
          ),
          const SizedBox(height: 8),

          _buildMenuCard(
            context: context,
            children: [
              FeatureGate(
                feature: AppFeature.statistiques,
                currentPlan: SubscriptionPlanExtension.fromString(profileState.value?.planAbonnement ?? 'BASIC'),
                child: _buildMenuItem(
                  context: context,
                  icon: Icons.analytics_outlined,
                  title: 'Statistiques avancées',
                  subtitle: 'Analyse des ventes, clients et IA',
                  onTap: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Bientôt disponible !'))),
                ),
              ),
              _buildDivider(),
              FeatureGate(
                feature: AppFeature.campagnes,
                currentPlan: SubscriptionPlanExtension.fromString(profileState.value?.planAbonnement ?? 'BASIC'),
                child: _buildMenuItem(
                  context: context,
                  icon: Icons.campaign_outlined,
                  title: 'Campagnes & Marketing',
                  subtitle: 'Newsletter, relances IA',
                  onTap: () => context.push('/marketing'),
                ),
              ),
              _buildDivider(),
              FeatureGate(
                feature: AppFeature.multiEmployes,
                currentPlan: SubscriptionPlanExtension.fromString(profileState.value?.planAbonnement ?? 'BASIC'),
                child: _buildMenuItem(
                  context: context,
                  icon: Icons.people_outline,
                  title: 'Multi-Employés',
                  subtitle: 'Gestion de l\'équipe et des accès',
                  onTap: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Bientôt disponible !'))),
                ),
              ),
              _buildDivider(),
              FeatureGate(
                feature: AppFeature.crm,
                currentPlan: SubscriptionPlanExtension.fromString(profileState.value?.planAbonnement ?? 'BASIC'),
                child: _buildMenuItem(
                  context: context,
                  icon: Icons.contact_page_outlined,
                  title: 'CRM Complet',
                  subtitle: 'Gestion poussée des fiches clients',
                  onTap: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Bientôt disponible !'))),
                ),
              ),
            ],
          ),

          const SizedBox(height: 20),

          // Sauvegarde & Export
          const Text(
            ' Sauvegarde & Export',
            style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey, fontSize: 13),
          ),
          const SizedBox(height: 8),

          _buildMenuCard(
            context: context,
            children: [
              _buildMenuItem(
                context: context,
                icon: Icons.cloud_upload_outlined,
                title: 'Google Drive & Exports',
                subtitle: 'Sauvegarde automatique et exports CSV',
                onTap: () => context.go('/profile/backup'),
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

          const SizedBox(height: 32),

          // Zone dangereuse
          const Text(
            ' Zone dangereuse',
            style: TextStyle(fontWeight: FontWeight.bold, color: Colors.red, fontSize: 13),
          ),
          const SizedBox(height: 8),

          _buildMenuCard(
            context: context,
            children: [
              _buildMenuItem(
                context: context,
                icon: Icons.delete_forever_outlined,
                title: 'Supprimer mon compte',
                subtitle: 'Libère votre numéro WhatsApp immédiatement.',
                onTap: () => context.go('/profile/delete_account'),
                iconColor: Colors.red,
                textColor: Colors.red,
              ),
            ],
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
    Color? iconColor,
    Color? textColor,
  }) {
    final themeColor = iconColor ?? Theme.of(context).colorScheme.primary;
    
    return ListTile(
      onTap: onTap,
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: themeColor.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, color: themeColor, size: 20),
      ),
      title: Text(title, style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15, color: textColor)),
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
