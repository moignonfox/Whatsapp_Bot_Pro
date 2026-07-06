import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../viewmodels/auth_notifier.dart';
import '../../viewmodels/profile_notifier.dart';
import '../../core/api/socket_client.dart';

/// Écran affiché aux utilisateurs inscrits mais pas encore validés par le Master.
class PendingValidationScreen extends ConsumerStatefulWidget {
  const PendingValidationScreen({super.key});

  @override
  ConsumerState<PendingValidationScreen> createState() => _PendingValidationScreenState();
}

class _PendingValidationScreenState extends ConsumerState<PendingValidationScreen> {
  Timer? _pollingTimer;

  @override
  void initState() {
    super.initState();
    // Lance un polling silencieux toutes les 10 secondes pour vérifier le statut du compte
    _pollingTimer = Timer.periodic(const Duration(seconds: 10), (timer) {
      ref.read(profileNotifierProvider.notifier).fetchProfile(silent: true);
    });
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    // On écoute le changement de statut pour rediriger automatiquement
    ref.listen(profileNotifierProvider, (previous, next) {
      if (next.value != null && next.value!.isApproved) {
        _pollingTimer?.cancel();
        if (context.mounted) {
          context.go('/today');
        }
      }
    });

    return Scaffold(
      backgroundColor: colorScheme.surface,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 28),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Animated icon
              TweenAnimationBuilder<double>(
                tween: Tween(begin: 0.8, end: 1.0),
                duration: const Duration(milliseconds: 800),
                curve: Curves.elasticOut,
                builder: (context, scale, child) => Transform.scale(scale: scale, child: child),
                child: Container(
                  width: 100,
                  height: 100,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        colorScheme.primary.withValues(alpha: 0.15),
                        colorScheme.secondary.withValues(alpha: 0.15),
                      ],
                    ),
                    shape: BoxShape.circle,
                    border: Border.all(color: colorScheme.primary.withValues(alpha: 0.3), width: 2),
                  ),
                  child: Icon(
                    Icons.hourglass_top_rounded,
                    size: 48,
                    color: colorScheme.primary,
                  ),
                ),
              ),
              const SizedBox(height: 32),

              // Title
              Text(
                'Demande envoyée !',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: colorScheme.onSurface,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),

              // Description
              Text(
                'Votre compte est en cours de validation par notre équipe. Vous recevrez une notification dès que votre accès sera activé.',
                style: TextStyle(
                  fontSize: 15,
                  color: colorScheme.onSurfaceVariant,
                  height: 1.6,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),

              // Info cards
              _buildInfoCard(
                context,
                icon: Icons.schedule_rounded,
                title: 'Délai de traitement',
                subtitle: 'Généralement moins de 24 heures',
                color: colorScheme.primary,
              ),
              const SizedBox(height: 12),
              _buildInfoCard(
                context,
                icon: Icons.celebration_rounded,
                title: 'Essai gratuit inclus',
                subtitle: '7 jours d\'accès Premium offerts Ã  l\'activation',
                color: const Color(0xFFFFC107),
              ),
              const SizedBox(height: 12),
              _buildInfoCard(
                context,
                icon: Icons.support_agent_rounded,
                title: 'Besoin d\'aide ?',
                subtitle: 'Contactez-nous via WhatsApp',
                color: const Color(0xFF25D366),
              ),

              const SizedBox(height: 40),

              // Logout button
              TextButton.icon(
                onPressed: () async {
                  await ref.read(authNotifierProvider.notifier).logout();
                  if (context.mounted) context.go('/login');
                },
                icon: const Icon(Icons.logout_rounded, size: 18),
                label: const Text('Se déconnecter'),
                style: TextButton.styleFrom(
                  foregroundColor: colorScheme.onSurfaceVariant,
                  textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoCard(BuildContext context, {
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
  }) {
    final colorScheme = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: isDark ? colorScheme.surfaceContainerHighest.withValues(alpha: 0.25) : colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(color: color.withValues(alpha: 0.15), shape: BoxShape.circle),
            child: Icon(icon, size: 20, color: color),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: colorScheme.onSurface)),
                const SizedBox(height: 2),
                Text(subtitle, style: TextStyle(fontSize: 12, color: colorScheme.onSurfaceVariant)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}


