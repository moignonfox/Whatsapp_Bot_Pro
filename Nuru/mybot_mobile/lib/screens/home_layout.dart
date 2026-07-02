import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../viewmodels/chat_notifier.dart';
import '../viewmodels/today_notifier.dart';
import 'package:go_router/go_router.dart';
import '../core/api/socket_client.dart';
import '../core/services/firebase_messaging_service.dart';

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

  void _goBranch(int index) {
    widget.navigationShell.goBranch(
      index,
      initialLocation: index == widget.navigationShell.currentIndex,
    );
  }

  @override
  Widget build(BuildContext context) {
    final orderState = ref.watch(todayNotifierProvider);
    int pendingOrders = 0;
    if (orderState.value != null) {
      for (var order in orderState.value!) {
        if (order.statut.toLowerCase() == 'en attente') {
          pendingOrders += 1;
        }
      }
    }
    final chatState = ref.watch(chatNotifierProvider);
    int totalUnread = 0;
    if (chatState.value != null) {
      for (var conv in chatState.value!) {
        totalUnread += conv.unreadCount;
      }
    }
    return Scaffold(
      body: widget.navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: widget.navigationShell.currentIndex,
        onDestinationSelected: _goBranch,
        destinations: [
          NavigationDestination(
            icon: Icon(Icons.space_dashboard_outlined),
            selectedIcon: Icon(Icons.space_dashboard),
            label: 'Accueil',
          ),
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
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings),
            label: 'Réglages',
          ),
        ],
      ),
    );
  }
}
