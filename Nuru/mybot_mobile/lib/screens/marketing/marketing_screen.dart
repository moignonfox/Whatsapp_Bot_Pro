import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
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
  String _selectedTarget = 'all';
  int _selectedTemplateIndex = 0;
  final List<TextEditingController> _variableControllers = [];
  final ImagePicker _picker = ImagePicker();
  String? _selectedImagePath;
  bool _isImprovingWithAI = false;
  bool _isUploadingImage = false;
  
  final List<Map<String, dynamic>> _templates = [
    {
      'name': 'vira_campagne_promo',
      'title': '🎉 Campagne promotionnelle',
      'variables': ['Nom de votre restaurant', 'Détail de votre offre (ex: -20% sur...)'],
      'hasImage': false,
    },
    {
      'name': 'vira_rappel_commande',
      'title': '🛍️ Rappel de commande',
      'variables': ['Nom de votre restaurant'],
      'hasImage': false,
    },
    {
      'name': 'rappel_client_inactif',
      'title': '👋 Relance client inactif',
      'variables': ['Nom de votre restaurant', 'Produit mis en avant'],
      'hasImage': true,
    },
  ];

  @override
  void initState() {
    super.initState();
    _updateVariableControllers();
  }

  void _updateVariableControllers() {
    for (var c in _variableControllers) {
      c.removeListener(_onVariableChanged);
      c.dispose();
    }
    _variableControllers.clear();
    final count = _templates[_selectedTemplateIndex]['variables'].length;
    for (int i = 0; i < count; i++) {
      final controller = TextEditingController();
      controller.addListener(_onVariableChanged);
      _variableControllers.add(controller);
    }
  }

  void _onVariableChanged() {
    setState(() {});
  }

  String _getTemplatePreview() {
    final templateName = _templates[_selectedTemplateIndex]['name'];
    String preview = "";
    
    if (templateName == 'vira_campagne_promo') {
      final var1 = _variableControllers.isNotEmpty && _variableControllers[0].text.isNotEmpty ? _variableControllers[0].text : "[Nom du restaurant]";
      final var2 = _variableControllers.length > 1 && _variableControllers[1].text.isNotEmpty ? _variableControllers[1].text : "[Détail de l'offre]";
      preview = "Bonjour Client,\n\nBonne nouvelle ! $var1 vous propose une offre spéciale :\n$var2\n\nN'hésitez pas à nous contacter ou à commander directement.\n\nÀ très bientôt !";
    } else if (templateName == 'vira_rappel_commande') {
      final var1 = _variableControllers.isNotEmpty && _variableControllers[0].text.isNotEmpty ? _variableControllers[0].text : "[Nom du restaurant]";
      preview = "Bonjour Client,\n\nNous espérons que vous avez apprécié votre dernière commande chez $var1.\nNous serions ravis de vous revoir bientôt pour de nouvelles saveurs.\n\nÀ très vite !";
    } else if (templateName == 'rappel_client_inactif') {
      final var1 = _variableControllers.isNotEmpty && _variableControllers[0].text.isNotEmpty ? _variableControllers[0].text : "[Nom du restaurant]";
      final var2 = _variableControllers.length > 1 && _variableControllers[1].text.isNotEmpty ? _variableControllers[1].text : "[Produit]";
      preview = "Bonjour Client,\n\nCela fait un moment que nous ne vous avons pas vu chez $var1 !\nPour vous donner l'eau à la bouche, avez-vous essayé notre $var2 ?\n\nNous espérons vous revoir très bientôt pour une délicieuse commande.\n\nExcellente journée !";
    }
    
    return preview;
  }

  @override
  void dispose() {
    for (var c in _variableControllers) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _pickImage() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery, imageQuality: 70);
    if (image != null) {
      setState(() {
        _selectedImagePath = image.path;
      });
    }
  }

  Future<void> _improveWithAI() async {
    if (_templates[_selectedTemplateIndex]['name'] != 'vira_campagne_promo' || _variableControllers.length < 2) return;
    
    final msg = _variableControllers[1].text.trim();
    if (msg.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Écrivez d\'abord un détail d\'offre à améliorer.')),
      );
      return;
    }
    setState(() => _isImprovingWithAI = true);
    try {
      final repo = ref.read(marketingRepositoryProvider);
      final improved = await repo.improveMessageWithAI(message: msg);
      if (!mounted) return;
      _variableControllers[1].text = improved;
      _variableControllers[1].selection = TextSelection.collapsed(offset: improved.length);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Row(
            children: [
              Icon(Icons.auto_awesome, color: Colors.white, size: 18),
              SizedBox(width: 10),
              Flexible(child: Text('Message amélioré avec succès !')),
            ],
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur : $e')));
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
    final hasImage = _templates[_selectedTemplateIndex]['hasImage'] == true;
    if (hasImage && _selectedImagePath == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Veuillez sélectionner une image.')));
      return;
    }
    
    for (var i = 0; i < _variableControllers.length; i++) {
      if (_variableControllers[i].text.trim().isEmpty) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Veuillez remplir la variable : ${_templates[_selectedTemplateIndex]['variables'][i]}')
        ));
        return;
      }
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
    final templateName = _templates[_selectedTemplateIndex]['name'] as String;
    
    // Le backend et Meta attendent les variables dans l'ordre du template.
    // D'après votre configuration, {{1}} est toujours le prénom.
    final variables = ["{prenom}", ..._variableControllers.map((c) => c.text.trim())];
    
    final hasImage = _templates[_selectedTemplateIndex]['hasImage'] == true;
    String? headerImageLink;

    if (hasImage && _selectedImagePath != null) {
      setState(() => _isUploadingImage = true);
      try {
        final repo = ref.read(marketingRepositoryProvider);
        headerImageLink = await repo.uploadCampaignImage(_selectedImagePath!);
      } catch (e) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur upload image: $e')));
        setState(() => _isUploadingImage = false);
        return;
      }
      setState(() => _isUploadingImage = false);
    }

    final success = await notifier.sendCampaign(
      templateName: templateName,
      variables: variables,
      headerImageLink: headerImageLink,
      target: _selectedTarget,
    );
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

                  // ── SECTION : MODÈLE WHATSAPP ──
                  _sectionLabel('📄 Modèle WhatsApp'),
                  const SizedBox(height: 10),
                  Container(
                    decoration: BoxDecoration(
                      color: isDark ? const Color(0xFF1A1A24) : Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: isDark ? Colors.white12 : Colors.grey.shade200),
                      boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.04), blurRadius: 10, offset: const Offset(0, 4))],
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<int>(
                        value: _selectedTemplateIndex,
                        isExpanded: true,
                        dropdownColor: isDark ? const Color(0xFF1A1A24) : Colors.white,
                        items: List.generate(_templates.length, (index) {
                          return DropdownMenuItem(
                            value: index,
                            child: Text(
                              _templates[index]['title'],
                              style: TextStyle(color: colorScheme.onSurface, fontWeight: FontWeight.w500),
                            ),
                          );
                        }),
                        onChanged: (val) {
                          if (val != null && val != _selectedTemplateIndex) {
                            setState(() {
                              _selectedTemplateIndex = val;
                              _updateVariableControllers();
                            });
                          }
                        },
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // ── SECTION : VARIABLES ──
                  if (_templates[_selectedTemplateIndex]['hasImage'] == true) ...[
                    _sectionLabel('🖼️ Image de la campagne'),
                    const SizedBox(height: 10),
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: InkWell(
                        onTap: _pickImage,
                        borderRadius: BorderRadius.circular(12),
                        child: Container(
                          width: double.infinity,
                          height: 120,
                          decoration: BoxDecoration(
                            color: isDark ? const Color(0xFF1A1A24) : Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: isDark ? Colors.white12 : Colors.grey.shade200),
                          ),
                          child: _selectedImagePath != null
                              ? ClipRRect(
                                  borderRadius: BorderRadius.circular(12),
                                  child: Image.file(File(_selectedImagePath!), fit: BoxFit.cover, width: double.infinity, height: 120),
                                )
                              : Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(Icons.add_photo_alternate_outlined, size: 32, color: colorScheme.primary.withValues(alpha: 0.7)),
                                    const SizedBox(height: 8),
                                    Text('Appuyez pour choisir une image', style: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 13)),
                                  ],
                                ),
                        ),
                      ),
                    ),
                  ],

                  if (_templates[_selectedTemplateIndex]['variables'].isNotEmpty) ...[
                    _sectionLabel('✍️ Variables du message'),
                    const SizedBox(height: 10),
                    ...List.generate(_templates[_selectedTemplateIndex]['variables'].length, (index) {
                      final variableLabel = _templates[_selectedTemplateIndex]['variables'][index];
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: Container(
                          decoration: BoxDecoration(
                            color: isDark ? const Color(0xFF1A1A24) : Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: isDark ? Colors.white12 : Colors.grey.shade200),
                          ),
                          child: TextField(
                            controller: _variableControllers[index],
                            style: TextStyle(fontSize: 14, color: colorScheme.onSurface),
                            maxLines: variableLabel.contains('Texte') ? 3 : (index == 1 && _templates[_selectedTemplateIndex]['name'] == 'vira_campagne_promo' ? 4 : 1),
                            decoration: InputDecoration(
                              labelText: variableLabel,
                              labelStyle: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 13),
                              border: InputBorder.none,
                              contentPadding: const EdgeInsets.all(16),
                            ),
                          ),
                        ),
                      );
                    }),
                    
                    if (_templates[_selectedTemplateIndex]['name'] == 'vira_campagne_promo') ...[
                      const SizedBox(height: 4),
                      Container(
                        width: double.infinity,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(12),
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
                            borderRadius: BorderRadius.circular(12),
                            onTap: _isImprovingWithAI ? null : _improveWithAI,
                            child: Padding(
                              padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
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
                                      _isImprovingWithAI ? 'Amélioration en cours...' : 'Améliorer l\'offre par IA',
                                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.deepPurple),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                    ],
                  ],

                  const SizedBox(height: 12),

                  // Aperçu
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: isDark ? const Color(0xFF1A1A24) : Colors.grey.shade50,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: isDark ? Colors.white10 : Colors.grey.shade300),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.visibility, size: 16, color: colorScheme.primary),
                            const SizedBox(width: 8),
                            Text('Aperçu du template sélectionné', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: colorScheme.primary)),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Container(
                          width: double.infinity,
                          margin: const EdgeInsets.only(right: 32),
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: isDark ? const Color(0xFF005C4B) : const Color(0xFFE7FFDB),
                            borderRadius: const BorderRadius.only(
                              topLeft: Radius.circular(12),
                              topRight: Radius.circular(12),
                              bottomRight: Radius.circular(12),
                              bottomLeft: Radius.circular(4),
                            ),
                            boxShadow: [
                              BoxShadow(color: Colors.black.withValues(alpha: 0.1), blurRadius: 2, offset: const Offset(0, 1)),
                            ],
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (_templates[_selectedTemplateIndex]['hasImage'] == true && _selectedImagePath != null)
                                Padding(
                                  padding: const EdgeInsets.only(bottom: 4.0),
                                  child: ClipRRect(
                                    borderRadius: BorderRadius.circular(8),
                                    child: Image.file(
                                      File(_selectedImagePath!),
                                      fit: BoxFit.cover,
                                      width: double.infinity,
                                      height: 140,
                                    ),
                                  ),
                                ),
                              Padding(
                                padding: const EdgeInsets.only(left: 6.0, right: 6.0, bottom: 6.0, top: 4.0),
                                child: Text(
                                  _getTemplatePreview(),
                                  style: TextStyle(
                                    fontSize: 14, 
                                    color: isDark ? Colors.white : Colors.black87, 
                                    height: 1.3,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          'Les variables seront remplies automatiquement pour chaque client.',
                          style: TextStyle(fontSize: 12, color: colorScheme.onSurfaceVariant, fontStyle: FontStyle.italic),
                        ),
                      ],
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
                              if (marketingState.isLoading || _isUploadingImage)
                                const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5))
                              else
                                const Icon(Icons.send_rounded, color: Colors.white, size: 22),
                              const SizedBox(width: 12),
                              Flexible(
                                child: Text(
                                  marketingState.isLoading || _isUploadingImage ? 'Envoi en cours...' : 'Lancer la campagne',
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
