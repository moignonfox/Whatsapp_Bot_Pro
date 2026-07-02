import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  Future<void> _launchRegistration() async {
    final Uri url = Uri.parse('https://tidal-unseen-abrasive.ngrok-free.dev/register');
    if (!await launchUrl(url, mode: LaunchMode.externalApplication)) {
      debugPrint('Could not launch $url');
    }
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: colorScheme.surface,
      body: Stack(
        children: [
          // Subtle, scattered abstract shapes (minimalist)
          Positioned(
            top: MediaQuery.of(context).size.height * 0.15,
            right: -20,
            child: _buildDecorativeBlob(colorScheme.primary.withOpacity(isDark ? 0.05 : 0.08), 120),
          ),
          Positioned(
            top: MediaQuery.of(context).size.height * 0.4,
            left: -40,
            child: _buildDecorativeBlob(const Color(0xFF25D366).withOpacity(isDark ? 0.04 : 0.06), 180),
          ),
          
          // Floating Emojis for a modern SaaS touch
          Positioned(
            top: MediaQuery.of(context).size.height * 0.2,
            left: 40,
            child: const Text('🤖', style: TextStyle(fontSize: 32)),
          ),
          Positioned(
            top: MediaQuery.of(context).size.height * 0.35,
            right: 50,
            child: const Text('✨', style: TextStyle(fontSize: 24)),
          ),

          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 40),
                  // Small Logo Badge
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF25D366).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Icon(
                      Icons.auto_awesome,
                      color: Color(0xFF25D366),
                      size: 28,
                    ),
                  ),
                  const SizedBox(height: 32),
                  
                  // Clean Typography
                  Text(
                    'Votre assistant\nWhatsApp intelligent.',
                    style: TextStyle(
                      fontSize: 40,
                      fontWeight: FontWeight.w800,
                      height: 1.1,
                      color: colorScheme.onSurface,
                      letterSpacing: -1.5,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Gérez vos commandes, répondez à vos clients et pilotez votre activité sans le moindre effort.',
                    style: TextStyle(
                      fontSize: 16,
                      color: colorScheme.onSurfaceVariant,
                      height: 1.5,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                  const Spacer(),
                  
                  // Minimalist Buttons
                  Column(
                    children: [
                      _buildPaintedButton(
                        text: 'Se connecter',
                        onTap: () => context.push('/login'),
                        isPrimary: true,
                      ),
                      const SizedBox(height: 16),
                      _buildPaintedButton(
                        text: 'Créer un compte',
                        onTap: _launchRegistration,
                        isPrimary: false,
                        colorScheme: colorScheme,
                      ),
                      const SizedBox(height: 24),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPaintedButton({
    required String text,
    required VoidCallback onTap,
    required bool isPrimary,
    ColorScheme? colorScheme,
  }) {
    return Container(
      width: double.infinity,
      height: 56,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(30),
        gradient: isPrimary
            ? const LinearGradient(
                colors: [Color(0xFF25D366), Color(0xFF128C7E)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              )
            : null,
        border: !isPrimary && colorScheme != null
            ? Border.all(color: colorScheme.outlineVariant.withOpacity(0.5), width: 1.5)
            : null,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(30),
          onTap: onTap,
          child: Center(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: isPrimary ? Colors.white : (colorScheme?.onSurface ?? Colors.black),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDecorativeBlob(Color color, double size) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: color,
        shape: BoxShape.circle,
      ),
    );
  }
}

