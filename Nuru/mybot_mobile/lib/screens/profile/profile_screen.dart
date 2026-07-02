import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../viewmodels/auth_notifier.dart';
import '../../viewmodels/profile_notifier.dart';
import '../../viewmodels/theme_notifier.dart';
import 'dart:convert';
import 'package:url_launcher/url_launcher.dart';
import '../../core/api/api_client.dart'; // To get the base URL if needed

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  final TextEditingController _promptController = TextEditingController();
  final TextEditingController _welcomeMsgController = TextEditingController();
  
  final Map<String, String> _dayLabels = {
    'lun': 'Lundi',
    'mar': 'Mardi',
    'mer': 'Mercredi',
    'jeu': 'Jeudi',
    'ven': 'Vendredi',
    'sam': 'Samedi',
    'dim': 'Dimanche',
  };

  final Map<String, Map<String, dynamic>> _horaires = {
    'lun': {'isOpen': false, 'open': '09:00', 'close': '18:00'},
    'mar': {'isOpen': false, 'open': '09:00', 'close': '18:00'},
    'mer': {'isOpen': false, 'open': '09:00', 'close': '18:00'},
    'jeu': {'isOpen': false, 'open': '09:00', 'close': '18:00'},
    'ven': {'isOpen': false, 'open': '09:00', 'close': '18:00'},
    'sam': {'isOpen': false, 'open': '09:00', 'close': '18:00'},
    'dim': {'isOpen': false, 'open': '09:00', 'close': '18:00'},
  };

  bool _isEditing = false;
  bool _isSaving = false;

  @override
  void dispose() {
    _promptController.dispose();
    _welcomeMsgController.dispose();
    super.dispose();
  }

  void _populateControllers(profile) {
    if (!_isEditing) {
      _promptController.text = profile.prompt;
      _welcomeMsgController.text = profile.msgConfirm;
      
      try {
        String rawJson = profile.horairesJson.replaceAll("'", '"');
        final decoded = jsonDecode(rawJson);
        if (decoded is Map) {
          for (var code in _horaires.keys) {
            var val = decoded[code];
            if (val is List && val.length >= 2) {
              _horaires[code]!['isOpen'] = true;
              _horaires[code]!['open'] = val[0].toString();
              _horaires[code]!['close'] = val[1].toString();
            } else {
              _horaires[code]!['isOpen'] = false;
            }
          }
        }
      } catch (e) {
        // Ignorer si invalide
      }
    }
  }

  Future<void> _saveProfile() async {
    setState(() => _isSaving = true);
    
    // Build horaires map in Web format: {"lun":["09:00","18:00"], "mar":[]}
    final Map<String, List<String>> horairesMap = {};
    for (var code in _horaires.keys) {
      if (_horaires[code]!['isOpen'] == true) {
        horairesMap[code] = [_horaires[code]!['open'].toString(), _horaires[code]!['close'].toString()];
      } else {
        horairesMap[code] = [];
      }
    }

    final success = await ref.read(profileNotifierProvider.notifier).updateProfile({
      'prompt': _promptController.text,
      'msg_confirm': _welcomeMsgController.text,
      'horaires_json': jsonEncode(horairesMap),
    });
    setState(() {
      _isSaving = false;
      if (success) _isEditing = false;
    });
    
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(success ? 'Paramètres mis à jour' : 'Erreur lors de la mise à jour'),
        backgroundColor: success ? const Color(0xFF25D366) : Colors.red,
      ),
    );
  }

  Future<void> _pickTime(String day, String type) async {
    final current = _horaires[day]![type] as String;
    final parts = current.split(':');
    TimeOfDay initial = const TimeOfDay(hour: 9, minute: 0);
    if (parts.length == 2) {
      initial = TimeOfDay(hour: int.tryParse(parts[0]) ?? 9, minute: int.tryParse(parts[1]) ?? 0);
    }
    final picked = await showTimePicker(
      context: context,
      initialTime: initial,
    );
    if (picked != null) {
      setState(() {
        final hh = picked.hour.toString().padLeft(2, '0');
        final mm = picked.minute.toString().padLeft(2, '0');
        _horaires[day]![type] = '$hh:$mm';
      });
    }
  }

  void _toggleEmergency(bool value, String nom) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(value ? 'Activer le bot' : 'Fermeture exceptionnelle'),
        content: Text(value 
            ? 'Le bot va recommencer à répondre automatiquement aux clients.' 
            : 'ATTENTION : Le bot sera immédiatement désactivé et ne répondra plus à aucun client jusqu\'à sa réactivation.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text('Annuler')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: value ? const Color(0xFF128C7E) : Colors.red),
            onPressed: () => Navigator.pop(context, true),
            child: Text('Confirmer', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final success = await ref.read(profileNotifierProvider.notifier).updateProfile({
        'is_active': value,
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? 'Statut mis à jour' : 'Erreur de mise à jour'),
          backgroundColor: success ? const Color(0xFF25D366) : Colors.red,
        ),
      );
    }
  }

  InputDecoration _inputDecoration(String label, String hint) {
    return InputDecoration(
      labelText: label,
      hintText: hint,
      labelStyle: TextStyle(color: Theme.of(context).textTheme.bodySmall?.color, fontSize: 13),
      hintStyle: TextStyle(color: Colors.grey.shade400, fontSize: 13),
      filled: true,
      fillColor: Theme.of(context).scaffoldBackgroundColor,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: const Color(0xFF128C7E), width: 1.5)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Text(
        title.toUpperCase(),
        style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Theme.of(context).textTheme.bodySmall?.color, letterSpacing: 0.5),
      ),
    );
  }

  Widget _buildContainer({required Widget child, Color? color, Border? border}) {
    return Container(
      decoration: BoxDecoration(
        color: color ?? Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        border: border,
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 10, offset: const Offset(0, 4))
        ],
      ),
      child: child,
    );
  }

  @override
  Widget build(BuildContext context) {
    final profileState = ref.watch(profileNotifierProvider);
    final themeMode = ref.watch(themeNotifierProvider);

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text('Réglages', style: TextStyle(fontWeight: FontWeight.w500)),
      ),
      body: profileState.when(
        loading: () => Center(child: CircularProgressIndicator(color: Color(0xFF128C7E))),
        error: (err, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Erreur: $err', style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 16),
              ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF128C7E)),
                onPressed: () => ref.read(profileNotifierProvider.notifier).fetchProfile(),
                child: Text('Réessayer', style: TextStyle(color: Colors.white)),
              )
            ],
          ),
        ),
        data: (profile) {
          if (profile == null) return Center(child: Text('Aucun profil trouvé', style: TextStyle(color: Colors.grey)));
          _populateControllers(profile);

          final domain = apiClient.options.baseUrl.replaceAll('/api/v1', '');
          final vitrineUrl = '$domain/v/${profile.id}';

          return SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // SECTION URGENCE
                _buildContainer(
                  color: profile.isActive 
                      ? Theme.of(context).cardColor 
                      : (Theme.of(context).brightness == Brightness.dark ? Colors.red.withAlpha(50) : Colors.red.shade50),
                  border: profile.isActive ? null : Border.all(color: Colors.red.shade200, width: 1),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.warning_amber_rounded, color: profile.isActive ? Colors.grey : Colors.red),
                            const SizedBox(width: 8),
                            const Text('Fermeture Exceptionnelle', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                          ],
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Désactive temporairement le bot (ex: urgence, inondation). Il ne répondra plus à aucun client.',
                          style: TextStyle(fontSize: 13, color: Colors.grey),
                        ),
                        const SizedBox(height: 12),
                        SwitchListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text(profile.isActive ? 'Bot Actif (En ligne)' : 'Bot Désactivé (Fermé)', 
                                 style: TextStyle(
                                   color: profile.isActive 
                                      ? (Theme.of(context).brightness == Brightness.dark ? const Color(0xFF25D366) : const Color(0xFF075E54)) 
                                      : Colors.red, 
                                   fontWeight: FontWeight.bold, fontSize: 14)),
                          value: profile.isActive,
                          activeThumbColor: const Color(0xFF25D366),
                          activeTrackColor: const Color(0xFF25D366).withAlpha(80),
                          inactiveThumbColor: Colors.red,
                          inactiveTrackColor: Colors.red.shade200,
                          onChanged: (val) => _toggleEmergency(val, profile.nom),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                // SECTION ABONNEMENT & BOUTIQUE
                _buildContainer(
                  color: Theme.of(context).cardColor,
                  child: ListTile(
                    leading: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(color: const Color(0xFFE8F5E9), borderRadius: BorderRadius.circular(8)),
                      child: Icon(Icons.storefront, color: Color(0xFF128C7E)),
                    ),
                    title: Text(profile.nom, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    subtitle: Text('Plan : ${profile.planAbonnement}', style: const TextStyle(color: Colors.grey)),
                  ),
                ),
                const SizedBox(height: 24),

                // SECTION APP SETTINGS
                _buildSectionTitle('Préférences'),
                _buildContainer(
                  child: Column(
                    children: [
                      ListTile(
                        leading: Icon(Icons.inventory_2, color: Colors.black54),
                        title: Text('Gérer le Catalogue', style: TextStyle(fontWeight: FontWeight.w500)),
                        subtitle: Text('Ajouter ou modifier des produits', style: TextStyle(fontSize: 12)),
                        trailing: Icon(Icons.chevron_right, color: Colors.grey),
                        onTap: () {
                          context.push('/catalog');
                        },
                      ),
                      const Divider(height: 1),
                      ListTile(
                        leading: Icon(Icons.dark_mode_outlined, color: Colors.black54),
                        title: Text('Thème Sombre', style: TextStyle(fontWeight: FontWeight.w500)),
                        trailing: DropdownButton<ThemeMode>(
                          value: themeMode,
                          underline: const SizedBox(),
                          icon: Icon(Icons.arrow_drop_down, color: Colors.grey),
                          style: TextStyle(color: Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black87, fontWeight: FontWeight.w500),
                          items: const [
                            DropdownMenuItem(value: ThemeMode.system, child: Text('Système')),
                            DropdownMenuItem(value: ThemeMode.light, child: Text('Clair')),
                            DropdownMenuItem(value: ThemeMode.dark, child: Text('Sombre')),
                          ],
                          onChanged: (mode) {
                            if (mode != null) {
                              ref.read(themeNotifierProvider.notifier).setThemeMode(mode);
                            }
                          },
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // SECTION VITRINE
                _buildSectionTitle('Ma Vitrine Web'),
                _buildContainer(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Row(
                      children: [
                        Expanded(
                          child: InkWell(
                            onTap: () async {
                              final uri = Uri.parse(vitrineUrl);
                              if (await canLaunchUrl(uri)) {
                                await launchUrl(uri, mode: LaunchMode.externalApplication);
                              } else {
                                if (context.mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Impossible d\'ouvrir le lien')));
                                }
                              }
                            },
                            child: Text(
                              vitrineUrl,
                              style: const TextStyle(color: Color(0xFF128C7E), decoration: TextDecoration.underline, fontSize: 14),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ),
                        Container(
                          decoration: BoxDecoration(color: Theme.of(context).scaffoldBackgroundColor, borderRadius: BorderRadius.circular(8)),
                          child: IconButton(
                            icon: Icon(Icons.copy, size: 20, color: Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black87),
                            onPressed: () {
                              Clipboard.setData(ClipboardData(text: vitrineUrl));
                              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Lien copié !')));
                            },
                          ),
                        )
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                // SECTION HORAIRES
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _buildSectionTitle('Horaires d\'ouverture'),
                    if (!_isEditing)
                      TextButton.icon(
                        icon: Icon(Icons.edit, size: 16, color: Color(0xFF128C7E)),
                        label: Text('Modifier', style: TextStyle(color: Color(0xFF128C7E), fontWeight: FontWeight.bold)),
                        onPressed: () => setState(() => _isEditing = true),
                      )
                  ],
                ),
                _buildContainer(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Builder(builder: (context) {
                      return Column(
                        children: _horaires.keys.map((code) {
                          final h = _horaires[code]!;
                          final dayLabel = _dayLabels[code]!;
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 12.0),
                            child: Row(
                              children: [
                                Transform.scale(
                                  scale: 0.8,
                                  child: Switch(
                                    value: h['isOpen'] as bool,
                                    activeThumbColor: const Color(0xFF25D366),
                                    activeTrackColor: const Color(0xFF25D366).withAlpha(80),
                                    onChanged: _isEditing ? (val) {
                                      setState(() { h['isOpen'] = val; });
                                    } : null,
                                  ),
                                ),
                                SizedBox(width: 80, child: Text(dayLabel, style: TextStyle(fontWeight: FontWeight.w500, color: (h['isOpen'] as bool) ? Colors.black87 : Colors.grey))),
                                if (h['isOpen'] == true)
                                  Expanded(
                                    child: Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                                      children: [
                                        InkWell(
                                          onTap: _isEditing ? () => _pickTime(code, 'open') : null,
                                          child: Container(
                                            padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                            decoration: BoxDecoration(color: Theme.of(context).scaffoldBackgroundColor, border: Border.all(color: _isEditing ? Colors.grey.shade300 : Colors.transparent), borderRadius: BorderRadius.circular(8)),
                                            child: Text(h['open'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                          )
                                        ),
                                        Text(' à ', style: TextStyle(color: Colors.grey)),
                                        InkWell(
                                          onTap: _isEditing ? () => _pickTime(code, 'close') : null,
                                          child: Container(
                                            padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                            decoration: BoxDecoration(color: Theme.of(context).scaffoldBackgroundColor, border: Border.all(color: _isEditing ? Colors.grey.shade300 : Colors.transparent), borderRadius: BorderRadius.circular(8)),
                                            child: Text(h['close'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                          )
                                        ),
                                      ],
                                    ),
                                  )
                                else
                                  const Expanded(child: Text(' Fermé', style: TextStyle(color: Colors.grey, fontStyle: FontStyle.italic))),
                              ],
                            ),
                          );
                        }).toList(),
                      );
                    }),
                  ),
                ),
                const SizedBox(height: 24),

                // SECTION PERSONNALISATION IA
                _buildSectionTitle('Personnalisation du Bot'),
                _buildContainer(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      children: [
                        TextField(
                          controller: _welcomeMsgController,
                          decoration: _inputDecoration('Message de Bienvenue / Confirmation', 'Ex: Bonjour ! Bienvenue chez nous...'),
                          maxLines: 3,
                          enabled: _isEditing,
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: _promptController,
                          decoration: _inputDecoration('Consignes de l\'IA (Prompt)', 'Ex: Tu es un assistant aimable. Réponds toujours poliment...'),
                          maxLines: 5,
                          enabled: _isEditing,
                        ),
                      ],
                    ),
                  ),
                ),
                
                if (_isEditing)
                  Padding(
                    padding: const EdgeInsets.only(top: 24.0),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () {
                              setState(() {
                                _isEditing = false;
                                _populateControllers(profile); // Reset
                              });
                            },
                            style: OutlinedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 16),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              side: BorderSide(color: Theme.of(context).dividerColor),
                            ),
                            child: Text('Annuler', style: TextStyle(color: Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black87, fontWeight: FontWeight.bold)),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: ElevatedButton(
                            onPressed: _isSaving ? null : _saveProfile,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF128C7E), 
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 16),
                              elevation: 0,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            ),
                            child: _isSaving 
                              ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) 
                              : Text('Enregistrer', style: TextStyle(fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ],
                    ),
                  ),

                const SizedBox(height: 48),

                // LOGOUT
                ElevatedButton.icon(
                  onPressed: () {
                    ref.read(authNotifierProvider.notifier).logout();
                  },
                  icon: Icon(Icons.logout),
                  label: Text('Se déconnecter', style: TextStyle(fontWeight: FontWeight.bold)),
                  style: ElevatedButton.styleFrom(
                    
                    foregroundColor: Colors.red,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Theme.of(context).colorScheme.error.withOpacity(0.5))),
                  ),
                ),
                const SizedBox(height: 32),
              ],
            ),
          );
        },
      ),
    );
  }
}
