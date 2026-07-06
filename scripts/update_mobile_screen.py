import os

dart_code = """import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../repositories/auth_repository.dart';

const List<Map<String, String>> kBusinessTypes = [
  {'value': 'restaurant', 'label': '🍽️ Restaurant / Café'},
  {'value': 'boutique', 'label': '🛍️ Boutique / Commerce'},
  {'value': 'sante', 'label': '🏥 Santé / Pharmacie'},
  {'value': 'beaute', 'label': '💅 Beauté / Salon'},
  {'value': 'services', 'label': '🔧 Services / Artisan'},
  {'value': 'education', 'label': '📚 Éducation / Formation'},
  {'value': 'immobilier', 'label': '🏠 Immobilier'},
  {'value': 'autre', 'label': '✨ Autre'},
];

const List<Map<String, String>> kDevises = [
  {'value': 'FCFA', 'label': 'FCFA (XOF)'},
  {'value': 'EUR', 'label': 'Euro (€)'},
  {'value': 'USD', 'label': 'Dollar (\$)'},
  {'value': 'MAD', 'label': 'Dirham (MAD)'},
  {'value': 'GHS', 'label': 'Cedi (GHS)'},
  {'value': 'NGN', 'label': 'Naira (NGN)'},
];

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  int _currentStep = 0;

  // Step 1 : Compte
  final _formKeyStep1 = GlobalKey<FormState>();
  final _ownerNameController = TextEditingController();
  final _ownerPhoneController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _botPhoneController = TextEditingController();
  bool _isPasswordVisible = false;

  // Step 2 : Identité
  final _formKeyStep2 = GlobalKey<FormState>();
  final _nomController = TextEditingController();
  final _locationController = TextEditingController();
  String _selectedBusinessType = 'boutique';
  String _selectedDevise = 'FCFA';

  // Step 3 : Configuration Bot
  final _businessInfoController = TextEditingController();
  final List<String> _selectedTasks = [
    'Prendre des commandes et vendre des produits',
    'Répondre aux questions fréquentes (FAQ)'
  ];
  String _selectedTone = 'Amical, accueillant et tutoiement si possible';

  bool _isLoading = false;
  String? _errorMessage;

  @override
  void dispose() {
    _ownerNameController.dispose();
    _ownerPhoneController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _botPhoneController.dispose();
    _nomController.dispose();
    _locationController.dispose();
    _businessInfoController.dispose();
    super.dispose();
  }

  void _onTaskChanged(String task, bool isChecked) {
    setState(() {
      if (isChecked) {
        if (!_selectedTasks.contains(task)) _selectedTasks.add(task);
      } else {
        _selectedTasks.remove(task);
      }
    });
  }

  Future<void> _submitForm() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      await ref.read(authRepositoryProvider).register(
        email: _emailController.text.trim().toLowerCase(),
        password: _passwordController.text,
        nom: _nomController.text.trim(),
        ownerName: _ownerNameController.text.trim(),
        ownerPhone: _ownerPhoneController.text.trim(),
        requestedBotPhone: _botPhoneController.text.trim(),
        businessType: _selectedBusinessType,
        devise: _selectedDevise,
        ville: _locationController.text.trim(),
        botTasks: _selectedTasks,
        tone: _selectedTone,
        businessInfo: _businessInfoController.text.trim(),
      );

      if (mounted) {
        context.go('/pending');
      }
    } catch (e) {
      setState(() => _errorMessage = e.toString().replaceAll('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: colorScheme.surface,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, color: colorScheme.onSurface),
          onPressed: () => context.go('/login'),
        ),
        title: Text('Créer votre Bot Vira', style: TextStyle(color: colorScheme.onSurface, fontWeight: FontWeight.bold)),
      ),
      body: SafeArea(
        child: Column(
          children: [
            if (_errorMessage != null)
              Container(
                margin: const EdgeInsets.all(16),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: colorScheme.error.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: colorScheme.error.withValues(alpha: 0.3)),
                ),
                child: Row(
                  children: [
                    Icon(Icons.error_outline_rounded, color: colorScheme.error, size: 20),
                    const SizedBox(width: 10),
                    Expanded(child: Text(_errorMessage!, style: TextStyle(color: colorScheme.error, fontSize: 13))),
                  ],
                ),
              ),
              
            Expanded(
              child: Theme(
                data: Theme.of(context).copyWith(
                  colorScheme: ColorScheme.light(primary: colorScheme.primary),
                ),
                child: Stepper(
                  type: StepperType.vertical,
                  currentStep: _currentStep,
                  onStepContinue: () {
                    if (_currentStep == 0) {
                      if (_formKeyStep1.currentState!.validate()) {
                        setState(() => _currentStep += 1);
                      }
                    } else if (_currentStep == 1) {
                      if (_formKeyStep2.currentState!.validate()) {
                        setState(() => _currentStep += 1);
                      }
                    } else if (_currentStep == 2) {
                      setState(() => _currentStep += 1);
                    } else if (_currentStep == 3) {
                      _submitForm();
                    }
                  },
                  onStepCancel: () {
                    if (_currentStep > 0) {
                      setState(() => _currentStep -= 1);
                    }
                  },
                  controlsBuilder: (context, details) {
                    final isLastStep = _currentStep == 3;
                    return Padding(
                      padding: const EdgeInsets.only(top: 24.0),
                      child: Row(
                        children: [
                          Expanded(
                            child: ElevatedButton(
                              onPressed: _isLoading ? null : details.onStepContinue,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: colorScheme.primary,
                                foregroundColor: colorScheme.onPrimary,
                                padding: const EdgeInsets.symmetric(vertical: 16),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              ),
                              child: _isLoading && isLastStep
                                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                  : Text(isLastStep ? 'Soumettre ma demande' : 'Continuer', style: const TextStyle(fontWeight: FontWeight.bold)),
                            ),
                          ),
                          if (_currentStep > 0) ...[
                            const SizedBox(width: 12),
                            Expanded(
                              child: OutlinedButton(
                                onPressed: _isLoading ? null : details.onStepCancel,
                                style: OutlinedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(vertical: 16),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                                ),
                                child: const Text('Retour'),
                              ),
                            ),
                          ],
                        ],
                      ),
                    );
                  },
                  steps: [
                    // STEP 1
                    Step(
                      title: const Text('Informations de connexion', style: TextStyle(fontWeight: FontWeight.bold)),
                      isActive: _currentStep >= 0,
                      state: _currentStep > 0 ? StepState.complete : StepState.indexed,
                      content: Form(
                        key: _formKeyStep1,
                        child: Column(
                          children: [
                            _buildField(controller: _ownerNameController, label: 'Nom complet (Gérant)', icon: Icons.person_outline),
                            const SizedBox(height: 12),
                            _buildField(controller: _ownerPhoneController, label: 'Votre téléphone', icon: Icons.phone_outlined, keyboardType: TextInputType.phone),
                            const SizedBox(height: 12),
                            _buildField(controller: _emailController, label: 'Adresse Email', icon: Icons.email_outlined, keyboardType: TextInputType.emailAddress),
                            const SizedBox(height: 12),
                            _buildPasswordField(controller: _passwordController, label: 'Mot de passe'),
                            const SizedBox(height: 12),
                            _buildField(controller: _botPhoneController, label: 'Numéro WhatsApp dédié au Bot', icon: Icons.smart_toy_outlined, keyboardType: TextInputType.phone),
                          ],
                        ),
                      ),
                    ),
                    
                    // STEP 2
                    Step(
                      title: const Text('Identité du Business', style: TextStyle(fontWeight: FontWeight.bold)),
                      isActive: _currentStep >= 1,
                      state: _currentStep > 1 ? StepState.complete : StepState.indexed,
                      content: Form(
                        key: _formKeyStep2,
                        child: Column(
                          children: [
                            _buildField(controller: _nomController, label: "Nom de l'entreprise", icon: Icons.storefront_outlined),
                            const SizedBox(height: 12),
                            _buildField(controller: _locationController, label: "Ville & Pays", icon: Icons.location_on_outlined),
                            const SizedBox(height: 12),
                            _buildDropdown(
                              label: "Type d'activité",
                              icon: Icons.category_outlined,
                              value: _selectedBusinessType,
                              items: kBusinessTypes,
                              onChanged: (v) => setState(() => _selectedBusinessType = v!),
                            ),
                            const SizedBox(height: 12),
                            _buildDropdown(
                              label: 'Devise',
                              icon: Icons.payments_outlined,
                              value: _selectedDevise,
                              items: kDevises,
                              onChanged: (v) => setState(() => _selectedDevise = v!),
                            ),
                          ],
                        ),
                      ),
                    ),
                    
                    // STEP 3
                    Step(
                      title: const Text('Configuration de l\'IA', style: TextStyle(fontWeight: FontWeight.bold)),
                      isActive: _currentStep >= 2,
                      state: _currentStep > 2 ? StepState.complete : StepState.indexed,
                      content: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Que voulez-vous que votre bot fasse ?', style: TextStyle(fontWeight: FontWeight.w600)),
                          const SizedBox(height: 8),
                          _buildCheckboxTile('Prendre des commandes et vendre des produits', Icons.shopping_cart),
                          _buildCheckboxTile('Gérer des réservations et des rendez-vous', Icons.calendar_today),
                          _buildCheckboxTile('Répondre aux questions fréquentes (FAQ)', Icons.help_outline),
                          _buildCheckboxTile('Proposer des promotions et relancer les clients', Icons.local_offer),
                          
                          const SizedBox(height: 20),
                          const Text('Ton de la conversation', style: TextStyle(fontWeight: FontWeight.w600)),
                          const SizedBox(height: 8),
                          _buildRadioTile('Amical, accueillant et tutoiement si possible', 'Amical & Chaleureux'),
                          _buildRadioTile('Formel, très professionnel et vouvoiement', 'Formel & Professionnel'),
                          
                          const SizedBox(height: 20),
                          TextFormField(
                            controller: _businessInfoController,
                            maxLines: 3,
                            decoration: InputDecoration(
                              labelText: 'Infos importantes (Horaires, règles...)',
                              alignLabelWithHint: true,
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                            ),
                          ),
                        ],
                      ),
                    ),
                    
                    // STEP 4
                    Step(
                      title: const Text('Aperçu & Lancement', style: TextStyle(fontWeight: FontWeight.bold)),
                      isActive: _currentStep >= 3,
                      content: Column(
                        children: [
                          Icon(Icons.auto_awesome, size: 48, color: colorScheme.primary),
                          const SizedBox(height: 16),
                          const Text(
                            'Votre bot est généré !',
                            style: TextStyle(fontSize: 20, fontWeight: bold),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Voici un aperçu de comment votre Assistant IA s\\'adressera à vos clients.',
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 24),
                          
                          // Chat Preview Bubble
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: isDark ? Colors.grey[900] : Colors.grey[100],
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(color: colorScheme.outlineVariant),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Align(
                                  alignment: Alignment.centerLeft,
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                    decoration: BoxDecoration(
                                      color: colorScheme.surfaceContainerHighest,
                                      borderRadius: const BorderRadius.only(
                                        topLeft: Radius.circular(16),
                                        topRight: Radius.circular(16),
                                        bottomRight: Radius.circular(16),
                                      ),
                                    ),
                                    child: Text('Bonjour', style: TextStyle(color: colorScheme.onSurface)),
                                  ),
                                ),
                                const SizedBox(height: 12),
                                Align(
                                  alignment: Alignment.centerRight,
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                    decoration: BoxDecoration(
                                      color: colorScheme.primary,
                                      borderRadius: const BorderRadius.only(
                                        topLeft: Radius.circular(16),
                                        topRight: Radius.circular(16),
                                        bottomLeft: Radius.circular(16),
                                      ),
                                    ),
                                    child: Text(
                                      _getPreviewText(),
                                      style: TextStyle(color: colorScheme.onPrimary),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _getPreviewText() {
    final name = _nomController.text.isEmpty ? "votre entreprise" : _nomController.text;
    if (_selectedTone.contains('Formel')) {
      return "Bonjour ! Bienvenue chez $name. Je suis l'assistant virtuel de l'établissement, disponible à toute heure. Que puis-je faire pour vous aujourd'hui ?";
    } else {
      return "Salut ! 👋 Bienvenue chez $name. Je suis l'assistant virtuel, là pour t'aider 24h/24. Comment je peux t'aider ? Commande, réservation, infos ?";
    }
  }

  Widget _buildField({required TextEditingController controller, required String label, required IconData icon, TextInputType? keyboardType}) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      validator: (v) => v == null || v.trim().isEmpty ? 'Champ requis' : null,
    );
  }

  Widget _buildPasswordField({required TextEditingController controller, required String label}) {
    return TextFormField(
      controller: controller,
      obscureText: !_isPasswordVisible,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: const Icon(Icons.lock_outline),
        suffixIcon: IconButton(
          icon: Icon(_isPasswordVisible ? Icons.visibility_off : Icons.visibility),
          onPressed: () => setState(() => _isPasswordVisible = !_isPasswordVisible),
        ),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      validator: (v) => v == null || v.length < 6 ? 'Minimum 6 caractères' : null,
    );
  }

  Widget _buildDropdown({required String label, required IconData icon, required String value, required List<Map<String, String>> items, required ValueChanged<String?> onChanged}) {
    return DropdownButtonFormField<String>(
      value: value,
      items: items.map((e) => DropdownMenuItem(value: e['value'], child: Text(e['label']!))).toList(),
      onChanged: onChanged,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
    );
  }

  Widget _buildCheckboxTile(String task, IconData icon) {
    final isChecked = _selectedTasks.contains(task);
    final colorScheme = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        border: Border.all(color: isChecked ? colorScheme.primary : colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(12),
        color: isChecked ? colorScheme.primary.withValues(alpha: 0.1) : Colors.transparent,
      ),
      child: CheckboxListTile(
        title: Text(task, style: const TextStyle(fontSize: 14)),
        secondary: Icon(icon, color: isChecked ? colorScheme.primary : null),
        value: isChecked,
        onChanged: (v) => _onTaskChanged(task, v!),
        activeColor: colorScheme.primary,
        controlAffinity: ListTileControlAffinity.leading,
        contentPadding: const EdgeInsets.symmetric(horizontal: 8),
      ),
    );
  }

  Widget _buildRadioTile(String value, String title) {
    final isSelected = _selectedTone == value;
    final colorScheme = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        border: Border.all(color: isSelected ? colorScheme.primary : colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(12),
        color: isSelected ? colorScheme.primary.withValues(alpha: 0.1) : Colors.transparent,
      ),
      child: RadioListTile<String>(
        title: Text(title, style: const TextStyle(fontSize: 14)),
        value: value,
        groupValue: _selectedTone,
        onChanged: (v) => setState(() => _selectedTone = v!),
        activeColor: colorScheme.primary,
        contentPadding: const EdgeInsets.symmetric(horizontal: 8),
      ),
    );
  }
}
"""

flutter_screen_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\Nuru\mybot_mobile\lib\screens\auth\register_screen.dart'

with open(flutter_screen_path, 'w', encoding='utf-8') as f:
    f.write(dart_code)

print("register_screen.dart written with Stepper implementation.")
