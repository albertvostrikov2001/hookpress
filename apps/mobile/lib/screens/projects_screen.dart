import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../l10n/app_localizations.dart';
import '../services/auth_service.dart';

class ProjectsScreen extends StatefulWidget {
  const ProjectsScreen({super.key});

  @override
  State<ProjectsScreen> createState() => _ProjectsScreenState();
}

class _ProjectsScreenState extends State<ProjectsScreen> {
  List<Map<String, dynamic>> _projects = [];
  bool _loading = true;
  bool _creating = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final api = context.read<AuthService>().api;
      final items = await api.listStudioProjects();
      if (mounted) {
        setState(() => _projects = items);
      }
    } catch (_) {
      if (mounted) {
        setState(() => _projects = []);
      }
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _create() async {
    setState(() => _creating = true);
    try {
      final api = context.read<AuthService>().api;
      await api.createStudioProject('Mobile demo ${DateTime.now().millisecond}');
      await _load();
    } finally {
      if (mounted) {
        setState(() => _creating = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Text(l10n.projectsTitle, style: Theme.of(context).textTheme.titleLarge),
              const Spacer(),
              if (_creating)
                const SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              else
                IconButton(onPressed: _create, icon: const Icon(Icons.add)),
            ],
          ),
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: _load,
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _projects.isEmpty
                    ? ListView(
                        children: [
                          SizedBox(
                            height: MediaQuery.of(context).size.height * 0.4,
                            child: Center(child: Text(l10n.projectsEmpty)),
                          ),
                        ],
                      )
                    : ListView.builder(
                        itemCount: _projects.length,
                        itemBuilder: (context, index) {
                          final p = _projects[index];
                          final status = p['status']?.toString() ?? '';
                          return Card(
                            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                            child: ListTile(
                              leading: CircleAvatar(
                                child: Text('${index + 1}'),
                              ),
                              title: Text(p['title']?.toString() ?? 'Project'),
                              subtitle: status.isNotEmpty ? Text(status) : null,
                              trailing: const Icon(Icons.chevron_right),
                            ),
                          );
                        },
                      ),
          ),
        ),
      ],
    );
  }
}
