import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'subscription_gate.dart';

/// Widget affichant un overlay "fonctionnalité verrouillée" si le plan
/// ne permet pas l'accès à [feature]. Sinon, affiche [child] normalement.
class FeatureGate extends StatelessWidget {
  final AppFeature feature;
  final SubscriptionPlan currentPlan;
  final Widget child;

  const FeatureGate({
    super.key,
    required this.feature,
    required this.currentPlan,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    if (feature.isAvailableFor(currentPlan)) return child;

    return Stack(
      children: [
        // Le contenu original en arrière-plan (grisé et flouté)
        AbsorbPointer(
          child: Opacity(opacity: 0.3, child: child),
        ),
        // Overlay de verrouillage
        Positioned.fill(
          child: GestureDetector(
            onTap: () => _showUpgradeDialog(context),
            child: Container(
              color: Colors.transparent,
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.surface.withValues(alpha: 0.95),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.4),
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.15),
                        blurRadius: 20,
                        offset: const Offset(0, 4),
                      )
                    ],
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('🔒', style: TextStyle(fontSize: 32)),
                      const SizedBox(height: 8),
                      Text(
                        feature.displayName,
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Disponible avec le plan ${feature.requiredPlan.label}',
                        style: TextStyle(
                          fontSize: 12,
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 12),
                      TextButton(
                        onPressed: () => _showUpgradeDialog(context),
                        style: TextButton.styleFrom(
                          backgroundColor: Theme.of(context).colorScheme.primary,
                          foregroundColor: Theme.of(context).colorScheme.onPrimary,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                        ),
                        child: const Text('Passer au niveau supérieur', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  void _showUpgradeDialog(BuildContext context) {
    final requiredPlan = feature.requiredPlan;
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            const Text('🔒 ', style: TextStyle(fontSize: 20)),
            Text('Fonctionnalité ${requiredPlan.label}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          ],
        ),
        content: Text(
          '${feature.displayName} est disponible uniquement avec le plan ${requiredPlan.label}.\n\n'
          'Contactez-nous pour activer votre forfait et débloquer cette fonctionnalité.',
          style: const TextStyle(fontSize: 14, height: 1.5),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Plus tard'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.pop(ctx);
              context.go('/profile/subscription');
            },
            child: const Text('Voir les offres'),
          ),
        ],
      ),
    );
  }
}
