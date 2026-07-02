import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../viewmodels/chat_notifier.dart';
import '../viewmodels/today_notifier.dart';
import '../viewmodels/profile_notifier.dart';
import 'package:go_router/go_router.dart';
import '../core/api/socket_client.dart';
import '../core/services/firebase_messaging_service.dart';
import '../core/subscription_gate.dart';

class HomeLayout extends ConsumerStatefulWidget {
  const HomeLayout({
    Key? key,
    required this.navigationShell,
  }) : super(key: key ?? const ValueKey<String>('HomeLayout'));

  final StatefulNavigationShell navigationShell;

  @override
  ConsumerState<HomeLayout> createState() => _HomeLayoutState();
}

class _HomeLayoutState extends ConsumerState<HomeLayout> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(socketClientProvider).init();
      ref.read(firebaseMessagingProvider).init();
    });
  }

  void _goBranch(int index, SubscriptionPlan plan) {
    // index 3 = Money (PRO+)
    if (index == 3 && !plan.isPro) {
      _showUpgradeSnack(AppFeature.paiements, plan);
      return;
    }
    widget.navigationShell.goBranch(
      index,
      initialLocation: index == widget.navigationShell.currentIndex,
    );
  }

  void _showUpgradeSnack(AppFeature feature, SubscriptionPlan plan) {
    final colorScheme = Theme.of(context).colorScheme;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Text('🔒 ', style: TextStyle(fontSize: 16)),
            Expanded(
              child: Text(
                '${feature.displayName} — Plan ${feature.requiredPlan.label} requis',
                style: const TextStyle(fontWeight: FontWeight.w500),
              ),
            ),
          ],
        ),
        action: SnackBarAction(
          label: 'Voir les offres',
          onPressed: () => context.go('/profile/subscription'),
        ),
        backgroundColor: colorScheme.inverseSurface,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        duration: const Duration(seconds: 3),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    final orderState = ref.watch(todayNotifierProvider);
    int pendingOrders = 0;
    if (orderState.value != null) {
      for (var order in orderState.value!) {
        if (order.statut.toLowerCase() == 'en attente') pendingOrders += 1;
      }
    }
    final chatState = ref.watch(chatNotifierProvider);
    int totalUnread = 0;
    if (chatState.value != null) {
      for (var conv in chatState.value!) { totalUnread += conv.unreadCount; }
    }

    // Get plan
    final profileState = ref.watch(profileNotifierProvider);
    final plan = profileState.hasValue && profileState.value != null
        ? SubscriptionPlanExtension.fromString(profileState.value!.planAbonnement)
        : SubscriptionPlan.basic;

    final bool moneyLocked = !plan.isPro;

    return Scaffold(
      body: widget.navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: widget.navigationShell.currentIndex,
        labelBehavior: NavigationDestinationLabelBehavior.alwaysHide,
        onDestinationSelected: (index) => _goBranch(index, plan),
        destinations: [
          // ── BASIC: Tableau de bord
          const NavigationDestination(
            icon: Icon(Icons.space_dashboard_outlined),
            selectedIcon: Icon(Icons.space_dashboard),
            label: 'Accueil',
          ),
          // ── BASIC: Commandes
          NavigationDestination(
            icon: Badge(
              isLabelVisible: pendingOrders > 0,
              label: Text(pendingOrders > 99 ? '99+' : pendingOrders.toString()),
              child: const Icon(Icons.shopping_bag_outlined),
            ),
            selectedIcon: Badge(
              isLabelVisible: pendingOrders > 0,
              label: Text(pendingOrders > 99 ? '99+' : pendingOrders.toString()),
              child: const Icon(Icons.shopping_bag),
            ),
            label: 'Commandes',
          ),
          // ── BASIC: Chat
          NavigationDestination(
            icon: Badge(
              isLabelVisible: totalUnread > 0,
              label: Text(totalUnread > 99 ? '99+' : totalUnread.toString()),
              child: const Icon(Icons.chat_outlined),
            ),
            selectedIcon: Badge(
              isLabelVisible: totalUnread > 0,
              label: Text(totalUnread > 99 ? '99+' : totalUnread.toString()),
              child: const Icon(Icons.chat),
            ),
            label: 'Messages',
          ),
          // ── PRO: Paiements / Finance
          NavigationDestination(
            icon: Stack(
              clipBehavior: Clip.none,
              children: [
                Icon(
                  Icons.account_balance_wallet_outlined,
                  color: moneyLocked ? colorScheme.onSurfaceVariant.withValues(alpha: 0.4) : null,
                ),
                if (moneyLocked)
                  Positioned(
                    right: -4,
                    top: -4,
                    child: Container(
                      width: 14,
                      height: 14,
                      decoration: BoxDecoration(
                        color: colorScheme.error,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.lock, size: 8, color: Colors.white),
                    ),
                  ),
              ],
            ),
            selectedIcon: Stack(
              clipBehavior: Clip.none,
              children: [
                Icon(
                  Icons.account_balance_wallet,
                  color: moneyLocked ? colorScheme.onSurfaceVariant.withValues(alpha: 0.4) : null,
                ),
                if (moneyLocked)
                  Positioned(
                    right: -4,
                    top: -4,
                    child: Container(
                      width: 14,
                      height: 14,
                      decoration: BoxDecoration(
                        color: colorScheme.error,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.lock, size: 8, color: Colors.white),
                    ),
                  ),
              ],
            ),
            label: 'Finance',
          ),
          // ── ALL: Réglages
          const NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings),
            label: 'Réglages',
          ),
        ],
      ),
    );
  }
}
