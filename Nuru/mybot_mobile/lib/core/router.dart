import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../screens/auth/welcome_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/home_layout.dart';
import '../screens/chat/chat_screen.dart';
import '../screens/chat/chat_detail_screen.dart';
import '../screens/today/today_screen.dart';
import '../screens/orders/orders_screen.dart';
import '../screens/catalog/catalog_screen.dart';
import '../screens/profile/profile_screen.dart';
import '../viewmodels/auth_notifier.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>();

final routerProvider = Provider<GoRouter>((ref) {
  final router = GoRouter(
    initialLocation: '/today',
    navigatorKey: _rootNavigatorKey,
    redirect: (context, state) {
      final authState = ref.read(authNotifierProvider);
      
      if (authState.isLoading) return null;

      final isAuth = authState.hasValue && authState.value == AuthStatus.authenticated;
      final isGoingToLogin = state.matchedLocation == '/login';
      final isGoingToWelcome = state.matchedLocation == '/welcome';

      if (!isAuth && !isGoingToLogin && !isGoingToWelcome) {
        return '/welcome';
      }
      if (isAuth && (isGoingToLogin || isGoingToWelcome)) {
        return '/today';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/welcome',
        builder: (context, state) => const WelcomeScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/catalog',
        builder: (context, state) => const CatalogScreen(),
      ),
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) {
          return HomeLayout(navigationShell: navigationShell);
        },
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/today',
                builder: (context, state) => const TodayScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/orders',
                builder: (context, state) => const OrdersScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/chat',
                builder: (context, state) => const ChatScreen(),
                routes: [
                  GoRoute(
                    path: 'detail/:waId',
                    builder: (context, state) {
                      final waId = state.pathParameters['waId']!;
                      final clientName = state.uri.queryParameters['clientName'] ?? waId;
                      return ChatDetailScreen(waId: waId, clientName: clientName);
                    },
                  ),
                ],
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/profile',
                builder: (context, state) => const ProfileScreen(),
              ),
            ],
          ),
        ],
      ),
    ],
  );

  ref.listen(authNotifierProvider, (previous, next) {
    router.refresh();
  });

  return router;
});
