import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../l10n/app_localizations.dart';
import '../services/auth_service.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final auth = context.watch<AuthService>();
    final user = auth.user;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        CircleAvatar(
          radius: 40,
          child: Text(
            (user?.displayName.isNotEmpty == true
                    ? user!.displayName[0]
                    : user?.email[0] ?? '?')
                .toUpperCase(),
            style: Theme.of(context).textTheme.headlineMedium,
          ),
        ),
        const SizedBox(height: 16),
        Text(
          user?.displayName.isNotEmpty == true
              ? user!.displayName
              : l10n.profileTitle,
          style: Theme.of(context).textTheme.titleLarge,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        Text(
          user?.email ?? '',
          style: Theme.of(context).textTheme.bodyMedium,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 24),
        Card(
          child: Column(
            children: [
              ListTile(
                leading: const Icon(Icons.badge_outlined),
                title: Text(l10n.profileRoles),
                subtitle: Text(
                  user?.roles.join(', ') ?? l10n.profileNoRoles,
                ),
              ),
              const Divider(height: 1),
              ListTile(
                leading: const Icon(Icons.key_outlined),
                title: Text(l10n.profileSession),
                subtitle: Text(
                  auth.refreshToken != null
                      ? l10n.profileSessionActive
                      : l10n.profileSessionMissing,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        FilledButton.tonalIcon(
          onPressed: () => auth.logout(),
          icon: const Icon(Icons.logout),
          label: Text(l10n.logoutButton),
        ),
      ],
    );
  }
}
