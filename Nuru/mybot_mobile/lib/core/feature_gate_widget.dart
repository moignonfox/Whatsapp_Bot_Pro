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
        // Overlay de verrouillage (simple pour éviter l'overflow)
        Positioned.fill(
          child: GestureDetector(
            onTap: () => _showUpgradeDialog(context),
            child: Container(
              color: Colors.transparent,
              alignment: Alignment.centerRight,
              padding: const EdgeInsets.only(right: 20),
              child: Icon(
                Icons.lock,
                color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
                size: 20,
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
