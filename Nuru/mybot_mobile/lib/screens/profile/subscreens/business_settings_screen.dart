import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:convert';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter/services.dart';
import '../../../core/api/api_client.dart';
import '../../../viewmodels/profile_notifier.dart';
import '../../../models/business_profile.dart';

class BusinessSettingsScreen extends ConsumerStatefulWidget {
  const BusinessSettingsScreen({super.key});

  @override
  ConsumerState<BusinessSettingsScreen> createState() => _BusinessSettingsScreenState();
}

class _BusinessSettingsScreenState extends ConsumerState<BusinessSettingsScreen> {
  final TextEditingController _promptController = TextEditingController();
  final TextEditingController _welcomeMsgController = TextEditingController();
  
  final Map<String, String> _dayLabels = {
    'lun': 'Lundi', 'mar': 'Mardi', 'mer': 'Mercredi',
    'jeu': 'Jeudi', 'ven': 'Vendredi', 'sam': 'Samedi', 'dim': 'Dimanche',
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
  bool _isInitialized = false;
  bool _isActive = true;

  @override
  void dispose() {
    _promptController.dispose();
    _welcomeMsgController.dispose();
    super.dispose();
  }

  void _populateControllers(BusinessProfile profile) {
    if (!_isEditing && !_isInitialized) {
      _promptController.text = profile.prompt;
      _welcomeMsgController.text = profile.msgConfirm;
      _isActive = profile.isActive;
      
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
      _isInitialized = true;
    }
  }

  Future<void> _saveProfile() async {
    setState(() => _isSaving = true);
    
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
      'is_active': _isActive ? 1 : 0,
    });
    setState(() {
      _isSaving = false;
      if (success) _isEditing = false;
    });
  }

  Future<void> _pickTime(String code, String key) async {
    final initial = _horaires[code]![key].toString().split(':');
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay(hour: int.tryParse(initial[0]) ?? 9, minute: int.tryParse(initial[1]) ?? 0),
    );
    if (time != null) {
      setState(() {
        _horaires[code]![key] = '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
      });
    }
  }

  Widget _buildContainer({required Widget child}) {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.02), blurRadius: 10, offset: const Offset(0, 4))],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(16),
        clipBehavior: Clip.antiAlias,
        child: child,
      ),
    );
  }

  InputDecoration _inputDecoration(String label, String hint) {
    return InputDecoration(
      labelText: label,
      hintText: hint,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey.shade300)),
      filled: true,
      fillColor: _isEditing ? Theme.of(context).cardColor : Theme.of(context).scaffoldBackgroundColor,
    );
  }

  @override
  Widget build(BuildContext context) {
    final profileState = ref.watch(profileNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Business', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        centerTitle: true,
        actions: [
          if (profileState.hasValue)
            TextButton(
              onPressed: () {
                if (_isEditing) {
                  _saveProfile();
                } else {
                  setState(() => _isEditing = true);
                }
              },
              child: _isSaving
                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                : Text(_isEditing ? 'Enregistrer' : 'Modifier'),
            )
        ],
      ),
      body: profileState.when(
        data: (profile) {
          if (profile == null) return const Center(child: Text('Erreur de chargement'));
          _populateControllers(profile);
          return SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _buildContainer(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text('Activer le Bot', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                            Switch(
                              value: _isActive,
                              activeThumbColor: Theme.of(context).colorScheme.primary,
                              onChanged: _isEditing ? (val) {
                                setState(() => _isActive = val);
                              } : null,
                            ),
                          ],
                        ),
                        if (!_isActive)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 16.0),
                            child: Text(
                              'Le bot est actuellement désactivé. Vous recevrez les messages mais le bot ne répondra pas automatiquement.',
                              style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.error),
                            ),
                          ),
                        const Divider(),
                        const SizedBox(height: 8),
                        const Text('Informations du commerce', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        const SizedBox(height: 16),
                        _buildInfoRow('Nom', profile.nom),
                        const Divider(),
                        _buildInfoRow('Devise', 'FCFA'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                
                const Padding(
                  padding: EdgeInsets.only(left: 4, bottom: 8),
                  child: Text('Votre Site Web / Catalogue', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                ),
                _buildContainer(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Partagez ce lien avec vos clients pour qu\'ils puissent voir vos produits et commander en ligne.',
                          style: TextStyle(fontSize: 13, color: Theme.of(context).colorScheme.onSurfaceVariant),
                        ),
                        const SizedBox(height: 16),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Theme.of(context).scaffoldBackgroundColor,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.grey.shade300),
                          ),
                          child: Row(
                            children: [
                              Icon(Icons.link, color: Theme.of(context).colorScheme.primary, size: 20),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  '${apiClient.options.baseUrl.replaceAll('/api/v1', '')}/v/${profile.id}',
                                  style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: () {
                                  Clipboard.setData(ClipboardData(text: '${apiClient.options.baseUrl.replaceAll('/api/v1', '')}/v/${profile.id}'));
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Lien copié dans le presse-papier !')));
                                },
                                icon: const Icon(Icons.copy, size: 18),
                                label: const Text('Copier'),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: ElevatedButton.icon(
                                onPressed: () async{
                                  final url = Uri.parse('${apiClient.options.baseUrl.replaceAll('/api/v1', '')}/v/${profile.id}');
                                  if (await canLaunchUrl(url)) {
                                    await launchUrl(url, mode: LaunchMode.externalApplication);
                                  } else {
                                    if (context.mounted) {
                                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Impossible d\'ouvrir le lien.')));
                                    }
                                  }
                                },
                                icon: const Icon(Icons.open_in_browser, size: 18),
                                label: const Text('Ouvrir'),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                
                const Padding(
                  padding: EdgeInsets.only(left: 4, bottom: 8),
                  child: Text('Horaires d\'ouverture', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
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
                                    activeThumbColor: Theme.of(context).colorScheme.secondary,
                                    onChanged: _isEditing ? (val) {
                                      setState(() { h['isOpen'] = val; });
                                    } : null,
                                  ),
                                ),
                                SizedBox(width: 80, child: Text(dayLabel, style: TextStyle(fontWeight: FontWeight.w500, color: (h['isOpen'] as bool) ? Theme.of(context).textTheme.bodyLarge?.color : Colors.grey))),
                                if (h['isOpen'] == true)
                                  Expanded(
                                    child: Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                                      children: [
                                        InkWell(
                                          onTap: _isEditing ? () => _pickTime(code, 'open') : null,
                                          child: Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                            decoration: BoxDecoration(color: Theme.of(context).scaffoldBackgroundColor, border: Border.all(color: _isEditing ? Colors.grey.shade300 : Colors.transparent), borderRadius: BorderRadius.circular(8)),
                                            child: Text(h['open'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                          )
                                        ),
                                        const Text(' à ', style: TextStyle(color: Colors.grey)),
                                        InkWell(
                                          onTap: _isEditing ? () => _pickTime(code, 'close') : null,
                                          child: Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
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
                
                const Padding(
                  padding: EdgeInsets.only(left: 4, bottom: 8),
                  child: Text('Personnalisation du Bot', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                ),
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
              ],
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Erreur: $e')),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 13)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
        ],
      ),
    );
  }
}
