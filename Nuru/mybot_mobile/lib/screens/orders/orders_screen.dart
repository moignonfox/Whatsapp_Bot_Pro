import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../viewmodels/today_notifier.dart';
import '../../viewmodels/stats_notifier.dart';

class OrdersScreen extends ConsumerWidget {
  const OrdersScreen({super.key});

  String _formatDate(String? dateStr) {
    if (dateStr == null || dateStr.isEmpty) return '';
    try {
      final DateTime d = DateTime.parse(dateStr);
      return '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')} à ${d.hour.toString().padLeft(2, '0')}h${d.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return dateStr;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(todayNotifierProvider);

    return Scaffold(
      
      appBar: AppBar(
        title: Text('Commandes', style: TextStyle(fontWeight: FontWeight.w500)),
      ),
      body: state.when(
          loading: () => Center(child: CircularProgressIndicator(color: Theme.of(context).colorScheme.primary)),
          error: (error, _) => Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text('Erreur: $error', textAlign: TextAlign.center, style: const TextStyle(color: Colors.red)),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => ref.read(todayNotifierProvider.notifier).fetchOrders(),
                  style: ElevatedButton.styleFrom(backgroundColor: Theme.of(context).colorScheme.primary),
                  child: Text('Réessayer', style: TextStyle(color: Colors.white)),
                )
              ],
            ),
          ),
          data: (orders) {
            if (orders.isEmpty) {
              return ListView(
                children: const [
                  Padding(
                    padding: EdgeInsets.all(32.0),
                    child: Center(
                      child: Text(
                        'Aucune commande pour aujourd\'hui.',
                        style: TextStyle(color: Colors.grey, fontSize: 16),
                      ),
                    ),
                  ),
                ],
              );
            }

            final isDark = Theme.of(context).brightness == Brightness.dark;
    return ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 12),
              itemCount: orders.length,
              itemBuilder: (context, index) {
                final order = orders[index];
                
                Color statusColor = Colors.orange;
                Color statusBg = Colors.orange.shade50;
                if (order.statut.contains('Confirmé')) {
                  statusColor = Colors.blue;
                  statusBg = Colors.blue.shade50;
                }
                if (order.statut.contains('Prêt')) {
                  statusColor = Theme.of(context).colorScheme.secondary;
                  statusBg = const Color(0xFFE8F5E9);
                }
                if (order.statut.contains('Annulé')) {
                  statusColor = Colors.red;
                  statusBg = Colors.red.shade50;
                }

                return Card(
                  margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // HEADER: Avatar + Name + Status
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              flex: 2,
                              child: Row(
                                children: [
                                  CircleAvatar(
                                    radius: 18,
                                    backgroundColor: order.type == 'Réservation' ? Colors.purple.withValues(alpha: 0.1) : Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
                                    child: Icon(
                                      order.type == 'Réservation' ? Icons.calendar_month : Icons.shopping_bag_outlined,
                                      size: 18,
                                      color: order.type == 'Réservation' ? Colors.purple.shade400 : Theme.of(context).colorScheme.primary,
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          order.clientName,
                                          style: TextStyle(
                                            fontWeight: FontWeight.bold, 
                                            fontSize: 15,
                                            color: Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black87,
                                          ),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                        Row(
                                          children: [
                                            Flexible(
                                              child: Text(
                                                order.type,
                                                style: TextStyle(
                                                  color: Colors.grey.shade500,
                                                  fontSize: 11,
                                                  fontWeight: FontWeight.w500,
                                                ),
                                                overflow: TextOverflow.ellipsis,
                                              ),
                                            ),
                                            if (order.createdAt.isNotEmpty) ...[
                                              Text(' • ', style: TextStyle(color: Colors.grey.shade400, fontSize: 11)),
                                              Expanded(
                                                child: Text(
                                                  _formatDate(order.createdAt),
                                                  style: TextStyle(color: Colors.grey.shade500, fontSize: 11),
                                                  overflow: TextOverflow.ellipsis,
                                                ),
                                              ),
                                            ]
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 4),
                            Flexible(
                              flex: 1,
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: statusBg,
                                  borderRadius: BorderRadius.circular(20),
                                ),
                                child: Text(
                                  order.statut,
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    color: statusColor, 
                                    fontWeight: FontWeight.bold, 
                                    fontSize: 10, // slightly smaller text to fit
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            )
                          ],
                        ),
                        
                        const SizedBox(height: 16),
                        
                        // Affichage du type de commande (Programmée ou Immédiate)
                        if (order.dateHeureDebut != null && order.dateHeureDebut!.isNotEmpty) ...[
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(Icons.schedule, size: 16, color: isDark ? Colors.green.shade300 : Colors.green.shade600),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  'Programmée le : ${_formatDate(order.dateHeureDebut)}', 
                                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: isDark ? Colors.green.shade300 : Colors.green.shade700),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                        ] else ...[
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(Icons.bolt, size: 16, color: isDark ? Colors.orange.shade300 : Colors.orange.shade600),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  'Immédiate', 
                                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: isDark ? Colors.orange.shade300 : Colors.orange.shade600),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                        ],
                        
                        // DETAILS
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(Icons.notes_rounded, size: 16, color: Colors.grey.shade400),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                order.details, 
                                style: TextStyle(fontSize: 13, height: 1.4, color: isDark ? Colors.grey.shade300 : Colors.grey.shade700),
                              ),
                            ),
                          ],
                        ),
                        
                        const SizedBox(height: 16),
                        Divider(height: 1, color: Theme.of(context).dividerColor),
                        const SizedBox(height: 12),
                        
                        // FOOTER: Total + Actions
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Total',
                                  style: TextStyle(color: Colors.grey, fontSize: 11, fontWeight: FontWeight.w500),
                                ),
                                Text(
                                  '${order.montant.toInt()} F',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold, 
                                    fontSize: 16,
                                    color: Theme.of(context).colorScheme.secondary,
                                  ),
                                ),
                              ],
                            ),
                            
                            // ACTIONS
                            if (order.statut.contains('En attente'))
                              Row(
                                children: [
                                  TextButton(
                                    onPressed: () async {
                                      await ref.read(todayNotifierProvider.notifier).updateOrderStatus(order.id, 'Annulé ❌');
                                      ref.read(statsNotifierProvider.notifier).fetchStats();
                                    },
                                    child: Text('Refuser', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold, fontSize: 13)),
                                  ),
                                  const SizedBox(width: 4),
                                  ElevatedButton(
                                    onPressed: () async {
                                      await ref.read(todayNotifierProvider.notifier).updateOrderStatus(order.id, 'Confirmé ✅');
                                      ref.read(statsNotifierProvider.notifier).fetchStats();
                                    },
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: Theme.of(context).colorScheme.primary,
                                      foregroundColor: Colors.white,
                                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                                      elevation: 0,
                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                                    ),
                                    child: Text('Accepter', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                  ),
                                ],
                              )
                            else if (order.statut.contains('Confirmé'))
                              ElevatedButton(
                                onPressed: () async {
                                  await ref.read(todayNotifierProvider.notifier).updateOrderStatus(order.id, 'Prêt ✅');
                                  ref.read(statsNotifierProvider.notifier).fetchStats();
                                },
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Theme.of(context).colorScheme.secondary,
                                  foregroundColor: Colors.white,
                                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                                  elevation: 0,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                                ),
                                child: Text('Marquer Prêt', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                              )
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            );
          },
        ),
    );
  }
}

