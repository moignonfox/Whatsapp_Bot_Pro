import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../viewmodels/profile_notifier.dart';

class PersonalInfoScreen extends ConsumerStatefulWidget {
  const PersonalInfoScreen({super.key});

  @override
  ConsumerState<PersonalInfoScreen> createState() => _PersonalInfoScreenState();
}

class _PersonalInfoScreenState extends ConsumerState<PersonalInfoScreen> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _managerPhoneController = TextEditingController();
  
  bool _isEditing = false;
  bool _isSaving = false;
  bool _isInitialized = false;

  @override
  void dispose() {
    _emailController.dispose();
    _managerPhoneController.dispose();
    super.dispose();
  }

  void _populateControllers(profile) {
    if (!_isEditing) {
      if (_emailController.text != profile.email) {
        _emailController.text = profile.email;
      }
      if (_managerPhoneController.text != profile.ownerPhone) {
        _managerPhoneController.text = profile.ownerPhone;
      }
      _isInitialized = true;
    }
  }

  Future<void> _saveProfile() async {
    setState(() => _isSaving = true);
    
    final success = await ref.read(profileNotifierProvider.notifier).updateProfile({
      'email': _emailController.text,
      'owner_phone': _managerPhoneController.text,
    });
    
    setState(() {
      _isSaving = false;
      if (success) _isEditing = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final profileState = ref.watch(profileNotifierProvider);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Informations Personnelles', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
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
          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Center(
                child: CircleAvatar(
                  radius: 50,
                  backgroundColor: Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
                  child: Text(
                    profile.nom.isNotEmpty ? profile.nom.substring(0, 1).toUpperCase() : '?',
                    style: TextStyle(fontSize: 40, fontWeight: FontWeight.bold, color: Theme.of(context).colorScheme.primary),
                  ),
                ),
              ),
              const SizedBox(height: 32),
              _buildField(context, 'Nom du compte', profile.nom, enabled: false),
              const SizedBox(height: 16),
              _buildField(context, 'Adresse Email', _emailController.text, controller: _emailController, enabled: _isEditing),
              const SizedBox(height: 16),
              _buildField(context, 'Numéro du gérant', _managerPhoneController.text, controller: _managerPhoneController, enabled: _isEditing),
              const SizedBox(height: 16),
              _buildField(context, 'Numéro du bot WhatsApp', profile.requestedBotPhone.isNotEmpty ? profile.requestedBotPhone : 'Non renseigné', enabled: false),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Erreur: $e')),
      ),
    );
  }

  Widget _buildField(BuildContext context, String label, String value, {bool enabled = false, TextEditingController? controller}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey)),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          initialValue: controller == null ? value : null,
          enabled: enabled,
          decoration: InputDecoration(
            filled: true,
            fillColor: Theme.of(context).cardColor,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
          ),
        ),
      ],
    );
  }
}
