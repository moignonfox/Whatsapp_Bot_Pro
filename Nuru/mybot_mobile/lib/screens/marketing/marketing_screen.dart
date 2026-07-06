import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/subscription_gate.dart';
import '../../viewmodels/profile_notifier.dart';
import '../../viewmodels/marketing_notifier.dart';
import '../../repositories/marketing_repository.dart';

class MarketingScreen extends ConsumerStatefulWidget {
  const MarketingScreen({super.key});

  @override
  ConsumerState<MarketingScreen> createState() => _MarketingScreenState();
}

class _MarketingScreenState extends ConsumerState<MarketingScreen> {
  final TextEditingController _messageController = TextEditingController();
  String _selectedTarget = 'all';
  bool _isImprovingWithAI = false;

  @override
  void dispose() {
    _messageController.dispose();
    super.dispose();
  }

  void _insertPrenom() {
    final text = _messageController.text;
    final selection = _messageController.selection;
    if (selection.start >= 0 && selection.end >= 0) {
      final newText = text.replaceRange(selection.start, selection.end, '{prenom}');
      _messageController.text = newText;
      _messageController.selection = TextSelection.collapsed(offset: selection.start + 8);
    } else {
      _messageController.text = text + '{prenom} ';
    }
  }

  /// Appelle le backend Gemini pour améliorer le message
  Future<void> _improveWithAI() async {
    final msg = _messageController.text.trim();
    if (msg.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Écrivez d\'abord un message à améliorer.')),
      );
      return;
    }
    setState(() => _isImprovingWithAI = true);
    try {
      final repo = ref.read(marketingRepositoryProvider);
      final improved = await repo.improveMessageWithAI(message: msg);
      if (!mounted) return;
      _messageController.text = improved;
      _messageController.selection = TextSelection.collapsed(offset: improved.length);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Row(
            children: [
              Icon(Icons.auto_awesome, color: Colors.white, size: 18),
              SizedBox(width: 10),
              Text('Message amélioré par l\'IA !'),
            ],
          ),
          backgroundColor: Colors.deepPurple,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erreur : ${e.toString().replaceFirst('Exception: ', '')}'),
          backgroundColor: Colors.red.shade700,
        ),
      );
    } finally {
      if (mounted) setState(() => _isImprovingWithAI = false);
    }
  }

  Future<void> _showConfirmationDialog(int count) async {
    final int maxMinutes = (count * 25) ~/ 60;
    final durationStr = maxMinutes > 0 ? '~$maxMinutes minutes' : 'Moins d\'une minute';
    final now = DateTime.now();
    final endTime = now.add(Duration(minutes: maxMinutes));
    final String timeStr = "${endTime.hour.toString().padLeft(2, '0')}h${endTime.minute.toString().padLeft(2, '0')}";

    final bool? confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Récapitulatif avant envoi', style: TextStyle(fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('📨 Destinataires : $count clients', style: const TextStyle(fontSize: 15)),
            const SizedBox(height: 8),
            Text('⏱️ Durée estimée : $durationStr\n    (délais anti-spam inclus)', style: const TextStyle(fontSize: 13, color: Colors.grey)),
            const SizedBox(height: 8),
            Text('📅 Fin prévue : $timeStr', style: const TextStyle(fontSize: 13)),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.red.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.red.withValues(alpha: 0.2)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.warning_amber_rounded, color: Colors.red, size: 18),
                  SizedBox(width: 8),
                  Expanded(child: Text('Cette action est irréversible', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold, fontSize: 13))),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Annuler', style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.primary,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Confirmer l\'envoi', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      _sendCampaign();
    }
  }

  Future<void> _onLaunchCampaignPressed() async {
    if (_messageController.text.trim().isEmpty) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Veuillez saisir un message.')));
      return;
    }
    try {
      final repo = ref.read(marketingRepositoryProvider);
      final count = await repo.estimateCampaign(target: _selectedTarget);
      if (!mounted) return;
      if (count == 0) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Aucun client ne correspond à ce ciblage.')));
        return;
      }
      await _showConfirmationDialog(count);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  Future<void> _sendCampaign() async {
    final notifier = ref.read(marketingNotifierProvider.notifier);
    final success = await notifier.sendCampaign(_messageController.text, _selectedTarget);
    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Campagne lancée avec succès !')));
      context.pop();
    } else if (mounted) {
      final error = ref.read(marketingNotifierProvider).error;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error?.toString() ?? 'Erreur lors de l\'envoi')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final profileState = ref.watch(profileNotifierProvider);
    final colorScheme = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // ── Fix : on attend que le profil soit chargé avant de décider du plan ──
    final isProfileLoaded = profileState is AsyncData;
    // planAbonnement est une String → convertir en enum avant d'appeler .isPremium/.isPro
    final planString = profileState.value?.planAbonnement;
    final currentPlan = planString != null
        ? SubscriptionPlanExtension.fromString(planString)
        : null;
    final isPremiumUser = currentPlan?.isPremium ?? false;
    final isProOrHigher = currentPlan?.isPro ?? false;  // isPro = pro || premium

    final marketingState = ref.watch(marketingNotifierProvider);

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF0F0F14) : const Color(0xFFF5F5FA),
      appBar: AppBar(
        title: const Text('Nouvelle Campagne', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18, letterSpacing: -0.4)),
        elevation: 0,
        backgroundColor: Colors.transparent,
      ),
      body: !isProfileLoaded
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(18, 8, 18, 40),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [

                  // ── BADGE PLAN ACTIF ──
                  if (currentPlan != null)
                    Container(
                      margin: const EdgeInsets.only(bottom: 20),
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: isPremiumUser
                              ? [const Color(0xFFF59E0B), const Color(0xFFF97316)]
                              : isProOrHigher
                                  ? [const Color(0xFF6366F1), const Color(0xFF8B5CF6)]
                                  : [Colors.grey.shade400, Colors.grey.shade600],
                        ),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.workspace_premium_rounded, color: Colors.white, size: 16),
                          const SizedBox(width: 8),
                          Flexible(
                            child: Text(
                              'Plan ${currentPlan.label} — Fonctionnalités débloquées',
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                    ),

                  // ── SECTION : AUDIENCE ──
                  _sectionLabel('🎯 Audience ciblée'),
                  const SizedBox(height: 10),
                  Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.04), blurRadius: 10, offset: const Offset(0, 4))],
                    ),
                    clipBehavior: Clip.antiAlias,
                    child: Material(
                      color: isDark ? const Color(0xFF1A1A24) : Colors.white,
                      child: Column(
                        children: [
                          _buildAudienceOption(
                          title: 'Tous les clients',
                          subtitle: 'Jusqu\'à 100 pour Basic, 500 pour Pro+',
                          value: 'all',
                          isLocked: false,
                          colorScheme: colorScheme,
                        ),
                        _divider(),
                        _buildAudienceOption(
                          title: 'Clients Actifs (7 derniers jours)',
                          subtitle: 'Ayant interagi la semaine dernière',
                          value: 'active',
                          isLocked: !isProOrHigher,
                          lockedLabel: 'Plan Pro requis',
                          colorScheme: colorScheme,
                        ),
                        _divider(),
                        _buildAudienceOption(
                          title: 'Clients Inactifs (30 jours)',
                          subtitle: 'Idéal pour les relances promotionnelles',
                          value: 'inactive',
                          isLocked: !isPremiumUser,
                          lockedLabel: 'Plan Premium requis',
                          colorScheme: colorScheme,
                        ),
                      ],
                    ),
                  ),
                ),

                  // Message si des options sont verrouillées — uniquement si PAS premium
                  if (!isPremiumUser) ...[
                    const SizedBox(height: 8),
                    Text(
                      isPremiumUser
                          ? ''
                          : isProOrHigher
                              ? 'Passez en Premium pour débloquer le ciblage "Inactifs".'
                              : 'Passez en Pro ou Premium pour débloquer le ciblage avancé.',
                      style: TextStyle(fontSize: 12, color: colorScheme.primary),
                    ),
                  ],

                  const SizedBox(height: 26),

                  // ── SECTION : MESSAGE ──
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _sectionLabel('✍️ Message'),
                      TextButton.icon(
                        onPressed: _insertPrenom,
                        icon: const Icon(Icons.person_add_rounded, size: 15),
                        label: const Text('{prenom}', style: TextStyle(fontSize: 12)),
                        style: TextButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          backgroundColor: colorScheme.primary.withValues(alpha: 0.08),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),

                  // Zone de saisie
                  Container(
                    decoration: BoxDecoration(
                      color: isDark ? const Color(0xFF1A1A24) : Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: isDark ? Colors.white12 : Colors.grey.shade200),
                      boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.04), blurRadius: 10, offset: const Offset(0, 4))],
                    ),
                    child: TextField(
                      controller: _messageController,
                      maxLines: 7,
                      style: TextStyle(fontSize: 14, color: colorScheme.onSurface),
                      decoration: InputDecoration(
                        hintText: 'Ex: Bonjour {prenom}, profitez de -20% aujourd\'hui sur notre nouveau catalogue !',
                        hintStyle: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 13),
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.all(16),
                      ),
                    ),
                  ),

                  const SizedBox(height: 12),

                  // ── BOUTON AMÉLIORER PAR IA ──
                  Container(
                    width: double.infinity,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(16),
                      gradient: LinearGradient(
                        colors: [
                          Colors.deepPurple.withValues(alpha: 0.1),
                          Colors.purpleAccent.withValues(alpha: 0.05)
                        ],
                      ),
                      border: Border.all(color: Colors.deepPurple.withValues(alpha: 0.3), width: 1.5),
                    ),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(16),
                        onTap: _isImprovingWithAI ? null : _improveWithAI,
                        child: Padding(
                          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              if (_isImprovingWithAI)
                                const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.deepPurple))
                              else
                                const Icon(Icons.auto_awesome_rounded, size: 20, color: Colors.deepPurple),
                              const SizedBox(width: 12),
                              Flexible(
                                child: Text(
                                  _isImprovingWithAI ? 'Amélioration en cours...' : 'Améliorer par IA',
                                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.deepPurple),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // ── BOUTON LANCER ──
                  Container(
                    width: double.infinity,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(16),
                      gradient: LinearGradient(
                        colors: [colorScheme.primary, colorScheme.primary.withValues(alpha: 0.8)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      boxShadow: [
                        BoxShadow(color: colorScheme.primary.withValues(alpha: 0.3), blurRadius: 12, offset: const Offset(0, 6))
                      ],
                    ),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(16),
                        onTap: marketingState.isLoading ? null : _onLaunchCampaignPressed,
                        child: Padding(
                          padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 16),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              if (marketingState.isLoading)
                                const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5))
                              else
                                const Icon(Icons.send_rounded, color: Colors.white, size: 22),
                              const SizedBox(width: 12),
                              Flexible(
                                child: Text(
                                  marketingState.isLoading ? 'Envoi en cours...' : 'Lancer la campagne',
                                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _sectionLabel(String text) {
    return Text(text, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800, letterSpacing: -0.3));
  }

  Widget _divider() {
    return Divider(height: 1, color: Theme.of(context).brightness == Brightness.dark ? Colors.white10 : Colors.grey.shade100);
  }

  Widget _buildAudienceOption({
    required String title,
    required String subtitle,
    required String value,
    required bool isLocked,
    String? lockedLabel,
    required ColorScheme colorScheme,
  }) {
    return RadioListTile<String>(
      title: Row(
        children: [
          Flexible(child: Text(title, overflow: TextOverflow.ellipsis, style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14, color: isLocked ? colorScheme.onSurface.withValues(alpha: 0.4) : colorScheme.onSurface))),
          if (isLocked && lockedLabel != null) ...[
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.orange.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.lock_rounded, size: 11, color: Colors.orange),
                  const SizedBox(width: 3),
                  Text(lockedLabel, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Colors.orange)),
                ],
              ),
            ),
          ],
        ],
      ),
      subtitle: Text(subtitle, style: TextStyle(fontSize: 12, color: colorScheme.onSurfaceVariant)),
      value: value,
      groupValue: _selectedTarget,
      onChanged: isLocked ? null : (val) => setState(() => _selectedTarget = val!),
      activeColor: colorScheme.primary,
    );
  }
}
