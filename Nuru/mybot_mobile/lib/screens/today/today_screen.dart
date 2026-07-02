import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../viewmodels/stats_notifier.dart';
import '../../viewmodels/today_notifier.dart';
import '../../viewmodels/profile_notifier.dart';

class TodayScreen extends ConsumerWidget {
  const TodayScreen({super.key});

  String _formatDate() {
    final now = DateTime.now();
    final days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
    final months = ['janv', 'févr', 'mars', 'avr', 'mai', 'juin', 'juil', 'août', 'sept', 'oct', 'nov', 'déc'];
    return '${days[now.weekday - 1]} ${now.day} ${months[now.month - 1]}';
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsState = ref.watch(statsNotifierProvider);
    final todayState = ref.watch(todayNotifierProvider);
    final profileState = ref.watch(profileNotifierProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      
      body: CustomScrollView(
          slivers: [
            // HEADER
            SliverAppBar(
              pinned: true,
              elevation: 0,
              backgroundColor: Theme.of(context).appBarTheme.backgroundColor,
              titleSpacing: 16,
              title: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('meinBot', style: TextStyle(color: isDark ? Colors.white : Colors.black87, fontSize: 20, fontWeight: FontWeight.w800, letterSpacing: -0.5)),
                      Text('Tableau de bord', style: TextStyle(color: isDark ? Colors.white70 : Colors.black54, fontSize: 13, fontWeight: FontWeight.w500)),
                    ],
                  ),
                  Row(
                    children: [
                      profileState.when(
                        data: (profile) => profile != null ? Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: isDark ? const Color(0xFF064E3B).withValues(alpha: 0.5) : const Color(0xFFE8F5E9),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: isDark ? const Color(0xFF059669) : Colors.transparent),
                          ),
                          child: Row(
                            children: [
                              Container(
                                width: 6,
                                height: 6,
                                decoration: const BoxDecoration(color: Color(0xFF10B981), shape: BoxShape.circle),
                              ),
                              const SizedBox(width: 4),
                              Text(
                                profile.planAbonnement,
                                style: TextStyle(color: isDark ? const Color(0xFF10B981) : const Color(0xFF065F46), fontSize: 10, fontWeight: FontWeight.bold),
                              )
                            ],
                          ),
                        ) : const SizedBox(),
                        loading: () => const SizedBox(),
                        error: (_, __) => const SizedBox(),
                      ),
                      const SizedBox(width: 12),
                      CircleAvatar(
                        radius: 16,
                        backgroundColor: const Color(0xFF128C7E),
                        child: profileState.when(
                          data: (p) => Text(p?.nom.substring(0, 2).toUpperCase() ?? 'MB', style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
                          loading: () => const SizedBox(),
                          error: (_, __) => const Text('MB', style: TextStyle(color: Colors.white, fontSize: 12)),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

              // GREETING BAR
              SliverToBoxAdapter(
                child: Container(
                  color: const Color(0xFF128C7E),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Bonjour 👋 Voici votre résumé du jour',
                        style: TextStyle(color: Theme.of(context).cardColor, fontSize: 13, fontWeight: FontWeight.w500),
                      ),
                      Text(
                        _formatDate(),
                        style: const TextStyle(color: Colors.white70, fontSize: 11),
                      ),
                    ],
                  ),
                ),
              ),

              // CONTENT
              SliverPadding(
                padding: const EdgeInsets.all(12),
                sliver: SliverList(
                  delegate: SliverChildListDelegate([
                    // FILTER PILLS
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
                      child: Row(
                        children: [
                          _buildFilterChip(context, 'Aujourd\'hui', 'today', ref),
                          const SizedBox(width: 8),
                          _buildFilterChip(context, '7 jours', 'week', ref),
                          const SizedBox(width: 8),
                          _buildFilterChip(context, 'Ce mois', 'month', ref),
                          const SizedBox(width: 8),
                          _buildFilterChip(context, 'Cette année', 'year', ref),
                        ],
                      ),
                    ),
                    const SizedBox(height: 4),

                    statsState.when(
                      data: (stats) => Padding(
                        padding: const EdgeInsets.only(left: 4, bottom: 8),
                        child: Text(
                          'ACTIVITÉ : ${stats.periodLabel.toUpperCase()}', 
                          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey, letterSpacing: 0.5)
                        ),
                      ),
                      loading: () => const SizedBox(),
                      error: (_, __) => const SizedBox(),
                    ),

                    // STATS GRID
                    statsState.when(
                      data: (stats) => GridView.count(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        crossAxisCount: 2,
                        crossAxisSpacing: 8,
                        mainAxisSpacing: 8,
                        childAspectRatio: 1.6,
                        children: [
                          _buildStatCard(context,
                              label: 'Chiffre d\'affaires',
                            value: '${stats.revenue.toInt()} F',
                            valueColor: const Color(0xFF075E54),
                            delta: 'Généré via chat',
                          ),
                          _buildStatCard(context,
                              label: 'Validées',
                            value: '${stats.ordersCount}',
                            valueColor: const Color(0xFF25D366),
                            delta: '${stats.pendingCount} en attente',
                          ),
                          _buildStatCard(context,
                              label: 'En attente',
                            value: '${stats.pendingCount}',
                            valueColor: Colors.orange,
                            delta: 'À traiter',
                          ),
                          _buildStatCard(context,
                              label: 'Annulées',
                            value: '${stats.cancellations}',
                            valueColor: Colors.red,
                            delta: 'Aujourd\'hui',
                          ),
                        ],
                      ),
                      loading: () => const SizedBox(height: 100, child: Center(child: CircularProgressIndicator())),
                      error: (err, _) => Center(child: Text('Erreur: $err')),
                    ),
                    const SizedBox(height: 8),

                    // AI CARD
                    profileState.when(
                      data: (profile) => Container(
                        margin: const EdgeInsets.symmetric(horizontal: 4),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Theme.of(context).cardColor,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: const Color(0xFF075E54),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Text(
                                (profile?.isActive ?? false) ? '🤖 IA active' : '⏸️ Bot en pause',
                                style: TextStyle(color: Theme.of(context).cardColor, fontSize: 11, fontWeight: FontWeight.w500),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    (profile?.isActive ?? false) ? 'Bot en ligne' : 'Fermeture exceptionnelle',
                                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black87),
                                  ),
                                  Text('Délégation', style: TextStyle(fontSize: 11, color: Colors.grey)),
                                ],
                              ),
                            ),
                            Text((profile?.isActive ?? false) ? '100%' : '0%', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF075E54))),
                          ],
                        ),
                      ),
                      loading: () => const SizedBox(),
                      error: (_, __) => const SizedBox(),
                    ),
                    const SizedBox(height: 12),

                    // QUICK ACTIONS
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 4),
                      child: Row(
                        children: [
                          _buildQuickAction(context, Icons.shopping_bag_outlined, 'Commandes', () => context.go('/orders')),
                          const SizedBox(width: 8),
                          _buildQuickAction(context, Icons.inventory_2_outlined, 'Catalogue', () => context.push('/catalog')),
                          const SizedBox(width: 8),
                          _buildQuickAction(context, Icons.campaign_outlined, 'Campagnes', () {}),
                          const SizedBox(width: 8),
                          _buildQuickAction(context, Icons.settings_outlined, 'Réglages', () => context.go('/profile')),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    Padding(
                      padding: EdgeInsets.only(left: 4, bottom: 8),
                      child: Text('DERNIÈRES COMMANDES', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey, letterSpacing: 0.5)),
                    ),

                    // ACTIVITY CARD
                    todayState.when(
                      data: (orders) {
                        if (orders.isEmpty) {
                          return Center(child: Padding(padding: EdgeInsets.all(16), child: Text('Aucune activité', style: TextStyle(color: Colors.grey))));
                        }
                        return Container(
                          margin: const EdgeInsets.symmetric(horizontal: 4),
                          decoration: BoxDecoration(
                            color: Theme.of(context).cardColor,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Column(
                            children: [
                              Padding(
                                padding: const EdgeInsets.all(12),
                                child: Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text('Activité récente', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                                    InkWell(
                                      onTap: () => context.go('/orders'),
                                      child: Text('Voir tout', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Color(0xFF25D366))),
                                    )
                                  ],
                                ),
                              ),
                              Divider(height: 1, color: Theme.of(context).dividerColor),
                              ...orders.take(3).map((order) {
                                Color dotColor = Colors.orange;
                                if (order.statut.contains('Confirmé') || order.statut.contains('Prêt')) dotColor = const Color(0xFF25D366);
                                else if (order.statut.contains('Annulé')) dotColor = Colors.red;

                                return Container(
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    border: Border(bottom: BorderSide(color: Theme.of(context).dividerColor)),
                                  ),
                                  child: Row(
                                    children: [
                                      Container(width: 8, height: 8, decoration: BoxDecoration(color: dotColor, shape: BoxShape.circle)),
                                      const SizedBox(width: 12),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(order.clientName, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                                            Text(order.details, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 11, color: Colors.grey)),
                                          ],
                                        ),
                                      ),
                                      const SizedBox(width: 8),
                                      Text('${order.montant.toInt()} F', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF075E54))),
                                    ],
                                  ),
                                );
                              }).toList(),
                            ],
                          ),
                        );
                      },
                      loading: () => Center(child: CircularProgressIndicator()),
                      error: (_, __) => Center(child: Text('Erreur chargement')),
                    ),
                    const SizedBox(height: 24),
                  ]),
                ),
              ),
            ],
          ),
    );
  }

  Widget _buildStatCard(BuildContext context, {required String label, required String value, required Color valueColor, required String delta}) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(label.toUpperCase(), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Colors.grey, letterSpacing: 0.3)),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: valueColor)),
          const SizedBox(height: 4),
          Text(delta, style: const TextStyle(fontSize: 10, color: Colors.grey)),
        ],
      ),
    );
  }

  Widget _buildQuickAction(BuildContext context, IconData icon, String label, VoidCallback onTap) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: [
              Icon(icon, size: 20, color: const Color(0xFF075E54)),
              SizedBox(height: 4),
              Text(label, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w500, color: Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black87)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFilterChip(BuildContext context, String label, String value, WidgetRef ref) {
    final active = ref.watch(statsPeriodProvider) == value;
    return GestureDetector(
      onTap: () => ref.read(statsPeriodProvider.notifier).setPeriod(value),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        decoration: BoxDecoration(
          color: active ? const Color(0xFF128C7E) : Colors.transparent,
          border: Border.all(color: active ? const Color(0xFF128C7E) : Colors.grey.withOpacity(0.3)),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: active ? Colors.white : (Theme.of(context).textTheme.bodyLarge?.color ??Colors.black87),
            fontSize: 12,
            fontWeight: active ? FontWeight.w600 : FontWeight.w500,
          ),
        ),
      ),
    );
  }
}


