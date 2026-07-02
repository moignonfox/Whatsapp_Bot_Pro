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
          // Elegant subtle blobs
          Positioned(
            top: MediaQuery.of(context).size.height * 0.1,
            right: -30,
            child: _buildDecorativeBlob(colorScheme.primary.withValues(alpha: isDark ? 0.15 : 0.1), 160),
          ),
          Positioned(
            bottom: MediaQuery.of(context).size.height * 0.15,
            left: -40,
            child: _buildDecorativeBlob(colorScheme.secondary.withValues(alpha: isDark ? 0.15 : 0.1), 200),
          ),
          SafeArea(
            child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight),
                child: IntrinsicHeight(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 24.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 40),
                        // Small Logo Badge
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: isDark ? Colors.white10 : Colors.white,
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: 0.05),
                                blurRadius: 10,
                                offset: const Offset(0, 4),
                              ),
                            ],
                          ),
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(12),
                            child: Image.asset(
                              'assets/icon.png',
                              width: 32,
                              height: 32,
                            ),
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
                              colorScheme: colorScheme,
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
              ),
            );
          },
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
    required ColorScheme colorScheme,
  }) {
    return Container(
      width: double.infinity,
      height: 56,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(30),
        gradient: isPrimary
            ? LinearGradient(
                colors: [colorScheme.primary, colorScheme.secondary],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              )
            : null,
        border: !isPrimary
            ? Border.all(color: colorScheme.outlineVariant.withValues(alpha: 0.5), width: 1.5)
            : null,
        boxShadow: isPrimary ? [
          BoxShadow(
            color: colorScheme.primary.withValues(alpha: 0.3),
            blurRadius: 12,
            offset: const Offset(0, 4),
          )
        ] : null,
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
                color: isPrimary ? Colors.white : colorScheme.onSurface,
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
        boxShadow: [
          BoxShadow(
            color: color,
            blurRadius: 40,
            spreadRadius: 20,
          ),
        ],
      ),
    );
  }
}
