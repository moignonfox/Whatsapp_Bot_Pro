import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:convert';
import '../../../viewmodels/profile_notifier.dart';

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

  @override
  void dispose() {
    _promptController.dispose();
    _welcomeMsgController.dispose();
    super.dispose();
  }

  void _populateControllers(profile) {
    if (!_isEditing && !_isInitialized) {
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
                                    activeColor: Theme.of(context).colorScheme.secondary,
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
