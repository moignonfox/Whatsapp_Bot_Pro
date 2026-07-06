import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../viewmodels/profile_notifier.dart';
import '../../../core/subscription_gate.dart';

class SubscriptionSettingsScreen extends ConsumerWidget {
  const SubscriptionSettingsScreen({super.key});

  String _formatDate(String isoDate) {
    if (isoDate.isEmpty) return 'Non définie';
    try {
      return DateFormat('dd/MM/yyyy').format(DateTime.parse(isoDate));
    } catch (_) {
      return isoDate;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colorScheme = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final profileState = ref.watch(profileNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Abonnement & Paiements',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        centerTitle: true,
      ),
      body: profileState.when(
        data: (profile) {
          if (profile == null) return const Center(child: Text('Erreur de chargement'));
          final plan = SubscriptionPlanExtension.fromString(profile.planAbonnement);

          return ListView(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
            children: [
              // ── En-tête : plan actif ───────────────────────────────
              _ActivePlanHeader(plan: plan, profile: profile, formatDate: _formatDate),
              const SizedBox(height: 28),

              // ── Comparatif des 3 offres ────────────────────────────
              _sectionLabel('🏷️ Toutes nos offres', colorScheme),
              const SizedBox(height: 12),
              _PlanCard.basic(current: plan),
              const SizedBox(height: 10),
              _PlanCard.pro(current: plan),
              const SizedBox(height: 10),
              _PlanCard.premium(current: plan),

              const SizedBox(height: 28),

              // ── Instructions de paiement (si non premium) ──────────
              if (plan != SubscriptionPlan.premium) ...[
                _sectionLabel('💳 Passer à l\'offre supérieure', colorScheme),
                const SizedBox(height: 12),
                _PaymentInstructions(isDark: isDark, colorScheme: colorScheme),
              ] else ...[
                _sectionLabel('🔄 Renouvellement', colorScheme),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: isDark
                        ? colorScheme.surfaceContainerHighest.withValues(alpha: 0.25)
                        : colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(
                    'Votre abonnement Premium est actif. Pour le renouveler, contactez-nous via WhatsApp ou envoyez le paiement habituel.',
                    style: TextStyle(fontSize: 14, height: 1.6, color: colorScheme.onSurfaceVariant),
                  ),
                ),
              ],
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Erreur: $e')),
      ),
    );
  }

  Widget _sectionLabel(String text, ColorScheme colorScheme) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 13, fontWeight: FontWeight.w700,
        color: colorScheme.onSurfaceVariant, letterSpacing: 0.3,
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// En-tête plan actif
// ─────────────────────────────────────────────────────────────────────────────
class _ActivePlanHeader extends StatelessWidget {
  final SubscriptionPlan plan;
  final dynamic profile;
  final String Function(String) formatDate;

  const _ActivePlanHeader({required this.plan, required this.profile, required this.formatDate});

  @override
  Widget build(BuildContext context) {
    switch (plan) {
      case SubscriptionPlan.premium:
        return _buildPremiumHeader(context);
      case SubscriptionPlan.pro:
        return _buildProHeader(context);
      case SubscriptionPlan.basic:
        return _buildBasicHeader(context);
    }
  }

  // ── PREMIUM : Fond noir, or, couronne ─────────────────────────────────────
  Widget _buildPremiumHeader(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF0d0d1a), Color(0xFF1a1a35), Color(0xFF0d1117)],
          begin: Alignment.topLeft, end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFFFD700).withValues(alpha: 0.5), width: 1.5),
        boxShadow: [
          BoxShadow(color: const Color(0xFFFFD700).withValues(alpha: 0.2), blurRadius: 24, offset: const Offset(0, 6)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(colors: [Color(0xFFFFD700), Color(0xFFFFA500)]),
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: [BoxShadow(color: const Color(0xFFFFD700).withValues(alpha: 0.4), blurRadius: 10)],
                ),
                child: const Text('👑', style: TextStyle(fontSize: 24)),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ShaderMask(
                      shaderCallback: (b) => const LinearGradient(
                        colors: [Color(0xFFFFD700), Color(0xFFFFF8DC), Color(0xFFFFD700)],
                      ).createShader(b),
                      child: const Text('Plan PREMIUM', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 22, letterSpacing: 1)),
                    ),
                    const Text('Automation + Cash', style: TextStyle(color: Colors.white38, fontSize: 12)),
                  ],
                ),
              ),
              _activeBadge(const Color(0xFF25D366)),
            ],
          ),
          _datesRow(profile, formatDate),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8, runSpacing: 6,
            children: const [
              _FeaturePill('✅ Prise de RDV', Colors.white54),
              _FeaturePill('✅ Statistiques', Colors.white54),
              _FeaturePill('✅ Paiement intégré', Color(0xFFFFD700)),
              _FeaturePill('✅ Multi-employés', Color(0xFFFFD700)),
              _FeaturePill('✅ Marketing avancé', Color(0xFFFFD700)),
              _FeaturePill('✅ CRM complet', Color(0xFFFFD700)),
            ],
          ),
        ],
      ),
    );
  }

  // ── PRO : Vert émeraude → Bleu électrique ─────────────────────────────────
  Widget _buildProHeader(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF0a5c38), Color(0xFF1a8a57), Color(0xFF0d4a8c)],
          begin: Alignment.topLeft, end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF25D366).withValues(alpha: 0.6), width: 1.5),
        boxShadow: [
          BoxShadow(color: const Color(0xFF25D366).withValues(alpha: 0.2), blurRadius: 20, offset: const Offset(0, 6)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF25D366).withValues(alpha: 0.25),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: const Color(0xFF25D366).withValues(alpha: 0.6)),
                ),
                child: const Icon(Icons.rocket_launch_rounded, color: Color(0xFF25D366), size: 26),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ShaderMask(
                      shaderCallback: (b) => const LinearGradient(
                        colors: [Color(0xFF25D366), Color(0xFF7FFFD4)],
                      ).createShader(b),
                      child: const Text('Plan PRO', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 22, letterSpacing: 1)),
                    ),
                    const Text('Business', style: TextStyle(color: Colors.white38, fontSize: 12)),
                  ],
                ),
              ),
              _activeBadge(const Color(0xFF25D366)),
            ],
          ),
          _datesRow(profile, formatDate),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8, runSpacing: 6,
            children: const [
              _FeaturePill('✅ Prise de RDV', Colors.white54),
              _FeaturePill('✅ Confirmation auto', Colors.white54),
              _FeaturePill('✅ Rappels auto', Color(0xFF25D366)),
              _FeaturePill('✅ Statistiques', Color(0xFF25D366)),
              _FeaturePill('✅ Gestion clients', Color(0xFF25D366)),
              _FeaturePill('✅ Campagnes', Color(0xFF25D366)),
            ],
          ),
        ],
      ),
    );
  }

  // ── BASIC : Épuré, neutre ──────────────────────────────────────────────────
  Widget _buildBasicHeader(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: isDark ? colorScheme.surfaceContainerHighest.withValues(alpha: 0.3) : colorScheme.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: colorScheme.outlineVariant.withValues(alpha: 0.5), width: 1.5),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.04), blurRadius: 12)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: colorScheme.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(Icons.bolt_rounded, color: colorScheme.primary, size: 26),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Plan BASIC', style: TextStyle(color: colorScheme.onSurface, fontWeight: FontWeight.w800, fontSize: 20)),
                    Text('Starter — Gratuit', style: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 12)),
                  ],
                ),
              ),
              _activeBadge(colorScheme.primary),
            ],
          ),
          // Dates avec couleurs adaptées au fond clair/sombre
          _datesRow(profile, formatDate, darkText: true),
        ],
      ),
    );
  }

  Widget _activeBadge(Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text('Actif', style: TextStyle(color: color, fontWeight: FontWeight.w700, fontSize: 11)),
    );
  }

  Widget _datesRow(dynamic profile, String Function(String) formatDate, {bool darkText = false}) {
    final debut = profile.dateDebutAbonnement ?? '';
    final fin = profile.dateFinAbonnement ?? '';
    if (debut.isEmpty && fin.isEmpty) return const SizedBox();
    // Couleur adaptative : blanc sur fond sombre, gris sur fond clair
    final textColor = darkText ? const Color(0xFF888888) : Colors.white54;
    final iconColor = darkText ? const Color(0xFFAAAAAA) : Colors.white38;
    return Column(
      children: [
        const SizedBox(height: 14),
        Container(height: 1, color: darkText ? Colors.black12 : Colors.white.withValues(alpha: 0.1)),
        const SizedBox(height: 12),
        Row(
          children: [
            if (debut.isNotEmpty) ...[
              Icon(Icons.play_circle_outline, color: iconColor, size: 14),
              const SizedBox(width: 4),
              Text('Début : ${formatDate(debut)}', style: TextStyle(color: textColor, fontSize: 12)),
            ],
            if (debut.isNotEmpty && fin.isNotEmpty) const SizedBox(width: 16),
            if (fin.isNotEmpty) ...[
              Icon(Icons.stop_circle_outlined, color: iconColor, size: 14),
              const SizedBox(width: 4),
              Text('Fin : ${formatDate(fin)}', style: TextStyle(color: textColor, fontSize: 12)),
            ],
          ],
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Carte comparatif d'un plan
// ─────────────────────────────────────────────────────────────────────────────
class _PlanCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final List<String> features;
  final List<String> lockedFeatures;
  final bool isCurrent;
  final Color accentColor;
  final Widget icon;
  final bool isLocked;

  const _PlanCard({
    required this.title,
    required this.subtitle,
    required this.features,
    required this.lockedFeatures,
    required this.isCurrent,
    required this.accentColor,
    required this.icon,
    this.isLocked = false,
  });

  factory _PlanCard.basic({required SubscriptionPlan current}) {
    return _PlanCard(
      title: 'BASIC',
      subtitle: 'Starter',
      accentColor: const Color(0xFF58A6FF),
      icon: const Icon(Icons.bolt_rounded, color: Color(0xFF58A6FF), size: 20),
      isCurrent: current == SubscriptionPlan.basic,
      isLocked: false,
      features: const ['Prise de RDV WhatsApp', 'Confirmation automatique', 'Dashboard simple'],
      lockedFeatures: const [],
    );
  }

  factory _PlanCard.pro({required SubscriptionPlan current}) {
    return _PlanCard(
      title: 'PRO',
      subtitle: 'Business — 20 000 FCFA/mois',
      accentColor: const Color(0xFF25D366),
      icon: const Icon(Icons.rocket_launch_rounded, color: Color(0xFF25D366), size: 20),
      isCurrent: current == SubscriptionPlan.pro,
      isLocked: current == SubscriptionPlan.basic,
      features: const ['Rappels automatiques', 'Statistiques avancées', 'Gestion clients', 'Campagnes simples'],
      lockedFeatures: const [],
    );
  }

  factory _PlanCard.premium({required SubscriptionPlan current}) {
    return _PlanCard(
      title: 'PREMIUM',
      subtitle: 'Automation + Cash — 40 000 FCFA/mois',
      accentColor: const Color(0xFFFFD700),
      icon: const Text('👑', style: TextStyle(fontSize: 18)),
      isCurrent: current == SubscriptionPlan.premium,
      isLocked: current != SubscriptionPlan.premium,
      features: const ['Paiement intégré', 'Marketing avancé', 'Multi-employés', 'CRM complet'],
      lockedFeatures: const [],
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final colorScheme = Theme.of(context).colorScheme;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isCurrent
            ? accentColor.withValues(alpha: isDark ? 0.12 : 0.08)
            : isDark
                ? colorScheme.surfaceContainerHighest.withValues(alpha: 0.2)
                : colorScheme.surfaceContainerHighest.withValues(alpha: 0.35),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isCurrent
              ? accentColor.withValues(alpha: 0.6)
              : colorScheme.outlineVariant.withValues(alpha: 0.3),
          width: isCurrent ? 2 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              icon,
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(title, style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: isCurrent ? accentColor : colorScheme.onSurface)),
                        if (isCurrent) ...[
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: accentColor.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(color: accentColor.withValues(alpha: 0.4)),
                            ),
                            child: Text('Votre plan', style: TextStyle(color: accentColor, fontSize: 10, fontWeight: FontWeight.w700)),
                          ),
                        ],
                        if (isLocked && !isCurrent) ...[
                          const SizedBox(width: 6),
                          Icon(Icons.lock_rounded, size: 13, color: colorScheme.onSurfaceVariant.withValues(alpha: 0.5)),
                        ],
                      ],
                    ),
                    Text(subtitle, style: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 11)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 6, runSpacing: 4,
            children: features.map((f) => _featurePill(f, accentColor, isLocked && !isCurrent, colorScheme, isDark)).toList(),
          ),
        ],
      ),
    );
  }

  Widget _featurePill(String label, Color color, bool locked, ColorScheme colorScheme, bool isDark) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(
        color: locked
            ? colorScheme.surfaceContainerHighest.withValues(alpha: 0.3)
            : color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: locked
              ? colorScheme.outlineVariant.withValues(alpha: 0.2)
              : color.withValues(alpha: 0.35),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            locked ? Icons.lock_outline_rounded : Icons.check_circle_outline_rounded,
            size: 11,
            color: locked ? colorScheme.onSurfaceVariant.withValues(alpha: 0.4) : color,
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w500,
              color: locked
                  ? colorScheme.onSurfaceVariant.withValues(alpha: 0.4)
                  : color.withValues(alpha: 0.9),
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Instructions de paiement
// ─────────────────────────────────────────────────────────────────────────────
class _PaymentInstructions extends StatelessWidget {
  final bool isDark;
  final ColorScheme colorScheme;

  const _PaymentInstructions({required this.isDark, required this.colorScheme});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: isDark
            ? colorScheme.surfaceContainerHighest.withValues(alpha: 0.25)
            : colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFFFD700).withValues(alpha: 0.25), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('💳', style: TextStyle(fontSize: 18)),
              const SizedBox(width: 10),
              Expanded(
                child: Text('Comment passer au niveau supérieur', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: colorScheme.onSurface)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Envoyez le paiement via T-Money ou Flooz au numéro du fondateur. Indiquez le nom de votre entreprise en motif du transfert.',
            style: TextStyle(fontSize: 13, height: 1.6, color: colorScheme.onSurfaceVariant),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFFFFD700).withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFFFFD700).withValues(alpha: 0.25)),
            ),
            child: Row(
              children: [
                const Text('⚡', style: TextStyle(fontSize: 16)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'PRO : 20 000 FCFA/mois • PREMIUM : 40 000 FCFA/mois',
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12, color: colorScheme.onSurface),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
          Text(
            'Votre compte sera mis à jour manuellement après réception du paiement.',
            style: TextStyle(fontSize: 11, color: colorScheme.onSurfaceVariant, fontStyle: FontStyle.italic),
          ),
        ],
      ),
    );
  }
}

class _FeaturePill extends StatelessWidget {
  final String label;
  final Color color;

  const _FeaturePill(this.label, this.color);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Text(label, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w500)),
    );
  }
}
