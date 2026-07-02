import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../repositories/auth_repository.dart';

// Liste des types de business
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

class _RegisterScreenState extends ConsumerState<RegisterScreen>
    with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _nomController = TextEditingController();
  final _ownerNameController = TextEditingController();
  final _ownerPhoneController = TextEditingController();
  final _botPhoneController = TextEditingController();

  String _selectedBusinessType = 'boutique';
  String _selectedDevise = 'FCFA';
  bool _isPasswordVisible = false;
  bool _isConfirmPasswordVisible = false;
  bool _isLoading = false;
  String? _errorMessage;

  late final AnimationController _animController;
  late final Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );
    _fadeAnim = CurvedAnimation(parent: _animController, curve: Curves.easeOut);
    _animController.forward();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _nomController.dispose();
    _ownerNameController.dispose();
    _ownerPhoneController.dispose();
    _botPhoneController.dispose();
    _animController.dispose();
    super.dispose();
  }

  Future<void> _register() async {
    if (!_formKey.currentState!.validate()) return;

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
      );

      if (mounted) {
        // Connexion automatique → aller vers l'écran d'attente
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
      body: FadeTransition(
        opacity: _fadeAnim,
        child: SafeArea(
          child: CustomScrollView(
            slivers: [
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 16),
                      // Back button
                      GestureDetector(
                        onTap: () => context.go('/login'),
                        child: Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            color: colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Icon(Icons.arrow_back_ios_new_rounded, size: 18, color: colorScheme.onSurface),
                        ),
                      ),
                      const SizedBox(height: 28),
                      // Header
                      ShaderMask(
                        shaderCallback: (bounds) => LinearGradient(
                          colors: [colorScheme.primary, colorScheme.secondary],
                        ).createShader(bounds),
                        child: const Text(
                          'Créer votre\ncompte',
                          style: TextStyle(
                            fontSize: 36,
                            fontWeight: FontWeight.w800,
                            color: Colors.white,
                            height: 1.15,
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Remplissez les informations ci-dessous. Votre compte sera activé par notre équipe sous 24h.',
                        style: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 14, height: 1.5),
                      ),
                      const SizedBox(height: 32),

                      if (_errorMessage != null) ...[
                        Container(
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
                        const SizedBox(height: 16),
                      ],

                      Form(
                        key: _formKey,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _sectionLabel('📋 Informations du compte'),
                            const SizedBox(height: 12),
                            _buildField(
                              controller: _emailController,
                              label: 'Adresse email (identifiant)',
                              icon: Icons.email_outlined,
                              keyboardType: TextInputType.emailAddress,
                              colorScheme: colorScheme,
                              isDark: isDark,
                              validator: (v) {
                                if (v == null || v.trim().isEmpty) return 'Champ requis';
                                final emailRegex = RegExp(r'^[\w\.\-]+@[\w\-]+\.\w+$');
                                if (!emailRegex.hasMatch(v.trim())) return 'Email invalide';
                                return null;
                              },
                            ),
                            const SizedBox(height: 12),
                            _buildPasswordField(
                              controller: _passwordController,
                              label: 'Mot de passe',
                              isVisible: _isPasswordVisible,
                              onToggle: () => setState(() => _isPasswordVisible = !_isPasswordVisible),
                              colorScheme: colorScheme,
                              isDark: isDark,
                              validator: (v) {
                                if (v == null || v.length < 6) return 'Minimum 6 caractères';
                                return null;
                              },
                            ),
                            const SizedBox(height: 12),
                            _buildPasswordField(
                              controller: _confirmPasswordController,
                              label: 'Confirmer le mot de passe',
                              isVisible: _isConfirmPasswordVisible,
                              onToggle: () => setState(() => _isConfirmPasswordVisible = !_isConfirmPasswordVisible),
                              colorScheme: colorScheme,
                              isDark: isDark,
                              validator: (v) {
                                if (v != _passwordController.text) return 'Les mots de passe ne correspondent pas';
                                return null;
                              },
                            ),

                            const SizedBox(height: 24),
                            _sectionLabel('🏪 Informations du business'),
                            const SizedBox(height: 12),
                            _buildField(
                              controller: _nomController,
                              label: 'Nom de votre boutique / entreprise',
                              icon: Icons.storefront_outlined,
                              colorScheme: colorScheme,
                              isDark: isDark,
                              validator: (v) => v == null || v.trim().isEmpty ? 'Champ requis' : null,
                            ),
                            const SizedBox(height: 12),
                            _buildDropdown(
                              label: 'Type de business',
                              icon: Icons.category_outlined,
                              value: _selectedBusinessType,
                              items: kBusinessTypes,
                              onChanged: (v) => setState(() => _selectedBusinessType = v!),
                              colorScheme: colorScheme,
                              isDark: isDark,
                            ),
                            const SizedBox(height: 12),
                            _buildDropdown(
                              label: 'Devise',
                              icon: Icons.payments_outlined,
                              value: _selectedDevise,
                              items: kDevises,
                              onChanged: (v) => setState(() => _selectedDevise = v!),
                              colorScheme: colorScheme,
                              isDark: isDark,
                            ),

                            const SizedBox(height: 24),
                            _sectionLabel('👤 Informations du gérant'),
                            const SizedBox(height: 12),
                            _buildField(
                              controller: _ownerNameController,
                              label: 'Votre nom complet',
                              icon: Icons.person_outline_rounded,
                              colorScheme: colorScheme,
                              isDark: isDark,
                              validator: (v) => v == null || v.trim().isEmpty ? 'Champ requis' : null,
                            ),
                            const SizedBox(height: 12),
                            _buildField(
                              controller: _ownerPhoneController,
                              label: 'Votre numéro personnel',
                              icon: Icons.phone_outlined,
                              keyboardType: TextInputType.phone,
                              colorScheme: colorScheme,
                              isDark: isDark,
                              validator: (v) => v == null || v.trim().isEmpty ? 'Champ requis' : null,
                            ),
                            const SizedBox(height: 12),
                            _buildField(
                              controller: _botPhoneController,
                              label: 'Numéro WhatsApp du bot (optionnel)',
                              icon: Icons.smart_toy_outlined,
                              keyboardType: TextInputType.phone,
                              colorScheme: colorScheme,
                              isDark: isDark,
                              validator: null,
                            ),

                            const SizedBox(height: 32),

                            // Submit button
                            GestureDetector(
                              onTap: _isLoading ? null : _register,
                              child: AnimatedContainer(
                                duration: const Duration(milliseconds: 200),
                                height: 58,
                                decoration: BoxDecoration(
                                  gradient: LinearGradient(
                                    colors: [colorScheme.primary, colorScheme.secondary],
                                    begin: Alignment.topLeft,
                                    end: Alignment.bottomRight,
                                  ),
                                  borderRadius: BorderRadius.circular(30),
                                  boxShadow: [
                                    BoxShadow(
                                      color: colorScheme.primary.withValues(alpha: 0.4),
                                      blurRadius: 16,
                                      offset: const Offset(0, 6),
                                    )
                                  ],
                                ),
                                child: Center(
                                  child: _isLoading
                                      ? const SizedBox(
                                          height: 24,
                                          width: 24,
                                          child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white),
                                        )
                                      : const Text(
                                          'Envoyer ma demande d\'inscription',
                                          style: TextStyle(
                                            color: Colors.white,
                                            fontWeight: FontWeight.w700,
                                            fontSize: 16,
                                          ),
                                        ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 16),
                            Center(
                              child: TextButton(
                                onPressed: () => context.go('/login'),
                                child: Text(
                                  'J\'ai déjà un compte',
                                  style: TextStyle(color: colorScheme.onSurfaceVariant, fontWeight: FontWeight.w500),
                                ),
                              ),
                            ),
                            const SizedBox(height: 32),
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
      ),
    );
  }

  Widget _sectionLabel(String text) {
    return Text(
      text,
      style: TextStyle(
        fontWeight: FontWeight.w700,
        fontSize: 14,
        color: Theme.of(context).colorScheme.primary,
        letterSpacing: 0.3,
      ),
    );
  }

  Widget _buildField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    required ColorScheme colorScheme,
    required bool isDark,
    TextInputType? keyboardType,
    String? Function(String?)? validator,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      validator: validator,
      style: TextStyle(color: colorScheme.onSurface, fontSize: 15, fontWeight: FontWeight.w500),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: colorScheme.onSurfaceVariant, size: 20),
        filled: true,
        fillColor: isDark
            ? colorScheme.surfaceContainerHighest.withValues(alpha: 0.25)
            : colorScheme.surfaceContainerHighest.withValues(alpha: 0.45),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: colorScheme.outlineVariant.withValues(alpha: 0.3)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: colorScheme.primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: colorScheme.error),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: colorScheme.error, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      ),
    );
  }

  Widget _buildPasswordField({
    required TextEditingController controller,
    required String label,
    required bool isVisible,
    required VoidCallback onToggle,
    required ColorScheme colorScheme,
    required bool isDark,
    String? Function(String?)? validator,
  }) {
    return TextFormField(
      controller: controller,
      obscureText: !isVisible,
      validator: validator,
      style: TextStyle(color: colorScheme.onSurface, fontSize: 15, fontWeight: FontWeight.w500),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(Icons.lock_outline_rounded, color: colorScheme.onSurfaceVariant, size: 20),
        suffixIcon: IconButton(
          onPressed: onToggle,
          icon: Icon(isVisible ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: colorScheme.onSurfaceVariant, size: 20),
        ),
        filled: true,
        fillColor: isDark
            ? colorScheme.surfaceContainerHighest.withValues(alpha: 0.25)
            : colorScheme.surfaceContainerHighest.withValues(alpha: 0.45),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: colorScheme.outlineVariant.withValues(alpha: 0.3)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: colorScheme.primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: colorScheme.error),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      ),
    );
  }

  Widget _buildDropdown({
    required String label,
    required IconData icon,
    required String value,
    required List<Map<String, String>> items,
    required ValueChanged<String?> onChanged,
    required ColorScheme colorScheme,
    required bool isDark,
  }) {
    return DropdownButtonFormField<String>(
      initialValue: value,
      onChanged: onChanged,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: colorScheme.onSurfaceVariant, size: 20),
        filled: true,
        fillColor: isDark
            ? colorScheme.surfaceContainerHighest.withValues(alpha: 0.25)
            : colorScheme.surfaceContainerHighest.withValues(alpha: 0.45),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: colorScheme.outlineVariant.withValues(alpha: 0.3)),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      ),
      dropdownColor: colorScheme.surface,
      items: items.map((item) => DropdownMenuItem<String>(
        value: item['value'],
        child: Text(item['label']!, style: TextStyle(color: colorScheme.onSurface, fontSize: 14)),
      )).toList(),
    );
  }
}
