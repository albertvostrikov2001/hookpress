import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';

class FeedScreen extends StatefulWidget {
  const FeedScreen({super.key});

  @override
  State<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> {
  late final ApiClient _api;
  List<Map<String, dynamic>> _articles = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    final auth = context.read<AuthService>();
    _api = auth.api;
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final items = await _api.listFeedArticles();
      if (mounted) {
        setState(() => _articles = items);
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _articles = [];
          _error = AppLocalizations.of(context)!.feedLoadError;
        });
      }
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(l10n.feedTitle, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: CircularProgressIndicator()),
            )
          else if (_error != null)
            Card(
              child: ListTile(
                leading: const Icon(Icons.error_outline),
                title: Text(_error!),
                trailing: IconButton(
                  icon: const Icon(Icons.refresh),
                  onPressed: _load,
                ),
              ),
            )
          else if (_articles.isEmpty)
            Card(
              child: ListTile(
                leading: const Icon(Icons.article_outlined),
                title: Text(l10n.feedEmpty),
              ),
            )
          else
            ..._articles.map((article) {
              final title = article['title']?.toString() ?? 'Article';
              final summary = article['summary']?.toString() ?? '';
              final likes = article['like_count']?.toString() ?? '0';
              return Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: const Icon(Icons.article),
                  title: Text(title),
                  subtitle: summary.isNotEmpty ? Text(summary) : null,
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.favorite_border, size: 16),
                      const SizedBox(width: 4),
                      Text(likes),
                    ],
                  ),
                ),
              );
            }),
        ],
      ),
    );
  }
}
