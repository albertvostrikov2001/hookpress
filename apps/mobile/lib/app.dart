import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';

import '../l10n/app_localizations.dart';
import '../services/auth_service.dart';
import 'chat_screen.dart';
import 'feed_screen.dart';
import 'login_screen.dart';
import 'player_screen.dart';
import 'profile_screen.dart';
import 'projects_screen.dart';

class HookPressApp extends StatelessWidget {
  const HookPressApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AuthService()..restoreSession(),
      child: MaterialApp(
        title: 'hook.press',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
          useMaterial3: true,
        ),
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        home: const _RootScreen(),
      ),
    );
  }
}

class _RootScreen extends StatelessWidget {
  const _RootScreen();

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    if (!auth.isAuthenticated) {
      return const LoginScreen();
    }
    return const _MainShell();
  }
}

class _MainShell extends StatefulWidget {
  const _MainShell();

  @override
  State<_MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<_MainShell> {
  int _index = 0;

  static const _screens = [
    FeedScreen(),
    ProjectsScreen(),
    ChatScreen(),
    PlayerScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.appTitle),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: l10n.logoutButton,
            onPressed: () => context.read<AuthService>().logout(),
          ),
        ],
      ),
      body: _screens[_index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.article_outlined),
            label: l10n.feedTitle,
          ),
          NavigationDestination(
            icon: const Icon(Icons.folder_outlined),
            label: l10n.projectsTitle,
          ),
          NavigationDestination(
            icon: const Icon(Icons.chat_outlined),
            label: l10n.chatTitle,
          ),
          NavigationDestination(
            icon: const Icon(Icons.play_circle_outline),
            label: l10n.playerTitle,
          ),
          NavigationDestination(
            icon: const Icon(Icons.person_outline),
            label: l10n.profileTitle,
          ),
        ],
      ),
    );
  }
}
