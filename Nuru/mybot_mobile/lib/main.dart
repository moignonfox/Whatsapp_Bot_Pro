import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:google_fonts/google_fonts.dart';
import 'core/router.dart';
import 'viewmodels/theme_notifier.dart';

@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  debugPrint("Handling a background message: ${message.messageId}");
}

// Configuration du channel haute priorité pour Android (Heads-up notification)
const AndroidNotificationChannel channel = AndroidNotificationChannel(
  'high_importance_channel', // id
  'High Importance Notifications', // title
  description: 'This channel is used for important notifications.', // description
  importance: Importance.max,
);

final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
    FlutterLocalNotificationsPlugin();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();

  // Création du channel pour que Android affiche la notification en haut de l'écran
  await flutterLocalNotificationsPlugin
      .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin>()
      ?.createNotificationChannel(channel);

  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

  runApp(
    const ProviderScope(
      child: MyApp(),
    ),
  );
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final goRouter = ref.watch(routerProvider);
    final themeMode = ref.watch(themeNotifierProvider);
    
    const Color primaryIndigo = Color(0xFF4F46E5);
    const Color accentSky = Color(0xFF0EA5E9);
    
    // Light Mode
    const Color lightBg = Color(0xFFF8FAFC);
    const Color lightCard = Colors.white;
    const Color lightText = Color(0xFF0F172A);
    
    // Dark Mode
    const Color darkBg = Color(0xFF0F172A);
    const Color darkCard = Color(0xFF1E293B);
    const Color darkText = Color(0xFFF8FAFC);

    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'Vira Mobile',
      themeMode: themeMode,
      theme: ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: lightBg,
        cardColor: lightCard,
        colorScheme: ColorScheme.fromSeed(
          seedColor: primaryIndigo,
          primary: primaryIndigo,
          secondary: accentSky,
          surface: lightBg,
          onSurface: lightText,
        ),
        textTheme: GoogleFonts.interTextTheme(ThemeData.light().textTheme),
        appBarTheme: const AppBarTheme(
          backgroundColor: lightBg,
          foregroundColor: lightText,
          elevation: 0,
        ),
        cardTheme: CardThemeData(
          elevation: 4,
          shadowColor: Colors.black.withOpacity(0.08),
          color: lightCard,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide.none,
          ),
        ),
        navigationBarTheme: NavigationBarThemeData(
          backgroundColor: lightCard,
          indicatorColor: primaryIndigo.withOpacity(0.15),
          iconTheme: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return const IconThemeData(color: primaryIndigo);
            }
            return IconThemeData(color: Colors.grey.shade400);
          }),
          labelTextStyle: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return const TextStyle(color: primaryIndigo, fontWeight: FontWeight.w600, fontSize: 12);
            }
            return TextStyle(color: Colors.grey.shade500, fontWeight: FontWeight.w400, fontSize: 12);
          }),
        ),
        dividerColor: Colors.black.withOpacity(0.05),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: darkBg,
        cardColor: darkCard,
        colorScheme: ColorScheme.fromSeed(
          brightness: Brightness.dark,
          seedColor: primaryIndigo,
          primary: primaryIndigo,
          secondary: accentSky,
          surface: darkBg,
          onSurface: darkText,
        ),
        textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
        appBarTheme: const AppBarTheme(
          backgroundColor: darkBg,
          foregroundColor: darkText,
          elevation: 0,
        ),
        cardTheme: CardThemeData(
          elevation: 8,
          shadowColor: Colors.black.withOpacity(0.3),
          color: darkCard,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide.none,
          ),
        ),
        navigationBarTheme: NavigationBarThemeData(
          backgroundColor: darkCard,
          indicatorColor: primaryIndigo.withOpacity(0.3),
          iconTheme: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return const IconThemeData(color: darkText);
            }
            return const IconThemeData(color: Colors.white30);
          }),
          labelTextStyle: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return const TextStyle(color: darkText, fontWeight: FontWeight.w600, fontSize: 12);
            }
            return const TextStyle(color: Colors.white30, fontWeight: FontWeight.w400, fontSize: 12);
          }),
        ),
        dividerColor: Colors.white.withOpacity(0.05),
        useMaterial3: true,
      ),
      routerConfig: goRouter,
    );
  }
}

