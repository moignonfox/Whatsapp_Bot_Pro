import 'package:flutter/material.dart';

class MoneyScreen extends StatefulWidget {
  const MoneyScreen({super.key});

  @override
  State<MoneyScreen> createState() => _MoneyScreenState();
}

class _MoneyScreenState extends State<MoneyScreen> {
  final bool isPremium = false;

  Future<void> _handleRefresh() async {
    await Future.delayed(const Duration(seconds: 1));
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Vue d\'ensemble',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: RefreshIndicator(
        onRefresh: _handleRefresh,
        child: ListView(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 16.0),
          children: [
            // --- HEADER: Overview ---
            Center(
              child: Column(
                children: [
                  Text(
                    '--- FCFA',
                    style: TextStyle(
                      fontSize: 42,
                      fontWeight: FontWeight.w900,
                      color: Colors.green.shade600,
                      letterSpacing: -1,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.orange.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.hourglass_empty, size: 14, color: Colors.orange.shade700),
                        const SizedBox(width: 6),
                        Text(
                          '--- FCFA en attente',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: Colors.orange.shade700,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.trending_up, size: 16, color: colorScheme.primary),
                      const SizedBox(width: 4),
                      Text(
                        '+--% par rapport à hier',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: colorScheme.primary,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // --- BALANCES (T-Money, Flooz) ---
            Row(
              children: [
                Expanded(
                  child: _buildBalanceCard(
                    context, 
                    title: 'T-Money', 
                    amount: '--- FCFA', 
                    icon: Icons.phone_android, 
                    color: Colors.blue
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildBalanceCard(
                    context, 
                    title: 'Flooz', 
                    amount: '--- FCFA', 
                    icon: Icons.phone_android, 
                    color: Colors.teal
                  ),
                ),
              ],
            ),

            const SizedBox(height: 32),

            // --- ACTIONS ---
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {},
                    style: ElevatedButton.styleFrom(
                      backgroundColor: isPremium ? colorScheme.primary : (isDark ? Colors.grey[800] : Colors.grey[200]),
                      foregroundColor: isPremium ? colorScheme.onPrimary : colorScheme.onSurfaceVariant,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      elevation: isPremium ? 2 : 0,
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(isPremium ? Icons.add_link : Icons.lock_outline, size: 18),
                        const SizedBox(width: 6),
                        Text(
                          isPremium ? 'Lien de paiement' : 'Lien (Premium)',
                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {},
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green.shade600,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      elevation: 2,
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: const [
                        Icon(Icons.account_balance, size: 18),
                        SizedBox(width: 6),
                        Text(
                          'Faire un retrait',
                          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _handleRefresh,
              icon: const Icon(Icons.refresh, size: 18),
              label: const Text('Actualiser les données', style: TextStyle(fontWeight: FontWeight.bold)),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                side: BorderSide(color: colorScheme.outlineVariant),
              ),
            ),

            const SizedBox(height: 40),

            // --- RECENT TRANSACTIONS ---
            Text(
              'Transactions Récentes',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: colorScheme.onSurface,
              ),
            ),
            const SizedBox(height: 16),
            
            _buildTransactionCard(
              context: context,
              icon: Icons.phone_android,
              iconColor: Colors.blue,
              title: 'Client - Commande #XXX',
              time: 'Date / Heure',
              amount: '--- FCFA',
              status: 'success',
            ),
            _buildTransactionCard(
              context: context,
              icon: Icons.credit_card,
              iconColor: Colors.purple,
              title: 'Client - Commande #XXX',
              time: 'Date / Heure',
              amount: '--- FCFA',
              status: 'pending',
            ),
            _buildTransactionCard(
              context: context,
              icon: Icons.phone_android,
              iconColor: Colors.teal,
              title: 'Client - Commande #XXX',
              time: 'Date / Heure',
              amount: '--- FCFA',
              status: 'failed',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBalanceCard(BuildContext context, {required String title, required String amount, required IconData icon, required Color color}) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 16, color: color),
              const SizedBox(width: 8),
              Text(title, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: color)),
            ],
          ),
          const SizedBox(height: 12),
          Text(amount, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18)),
        ],
      ),
    );
  }

  Widget _buildTransactionCard({
    required BuildContext context,
    required IconData icon,
    required Color iconColor,
    required String title,
    required String time,
    required String amount,
    required String status,
  }) {
    
    Color amountColor;
    TextDecoration? decoration;
    
    switch (status) {
      case 'success':
        amountColor = Colors.green.shade600;
        break;
      case 'pending':
        amountColor = Colors.orange.shade600;
        break;
      case 'failed':
      default:
        amountColor = Colors.grey;
        decoration = TextDecoration.lineThrough;
        break;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      elevation: 0,
      color: Theme.of(context).cardColor,
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: iconColor.withValues(alpha: 0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: iconColor, size: 24),
        ),
        title: Text(
          title,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
        ),
        subtitle: Text(
          time,
          style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant),
        ),
        trailing: Text(
          amount,
          style: TextStyle(
            fontWeight: FontWeight.w900,
            fontSize: 15,
            color: amountColor,
            decoration: decoration,
          ),
        ),
      ),
    );
  }
}
