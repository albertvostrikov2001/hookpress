import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../l10n/app_localizations.dart';
import '../services/auth_service.dart';
import '../services/chat_cache.dart';
import '../services/chat_ws_service.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key, this.cache});

  final ChatMessageStore? cache;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  late final ChatMessageStore _cache;
  final _controller = TextEditingController();
  ChatWsService? _ws;
  String? _roomId;
  List<Map<String, dynamic>> _messages = [];
  bool _loading = true;
  bool _offline = false;
  bool _wsConnected = false;

  @override
  void initState() {
    super.initState();
    _cache = widget.cache ?? ChatCache();
    _bootstrap();
  }

  @override
  void dispose() {
    _controller.dispose();
    _ws?.dispose();
    super.dispose();
  }

  Future<void> _bootstrap() async {
    setState(() => _loading = true);
    try {
      final api = context.read<AuthService>().api;
      final room = await api.createChatRoom(name: 'Mobile chat');
      _roomId = room['id'] as String;
      await _loadMessages();
      await _connectWs();
      if (mounted) {
        setState(() {
          _loading = false;
          _offline = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loading = false;
          _offline = true;
        });
      }
    }
  }

  Future<void> _loadMessages() async {
    if (_roomId == null) return;
    final cached = await _cache.loadMessages(_roomId!);
    try {
      final api = context.read<AuthService>().api;
      final remote = await api.listChatMessages(_roomId!);
      if (remote.isNotEmpty) {
        await _cache.saveMessages(_roomId!, remote);
      }
      if (mounted) {
        setState(() {
          _messages = remote.isNotEmpty ? remote : cached;
          _offline = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _messages = cached;
          _offline = true;
        });
      }
    }
  }

  Future<void> _connectWs() async {
    if (_roomId == null) return;
    await _ws?.dispose();
    final api = context.read<AuthService>().api;
    _ws = ChatWsService(
      wsUrl: api.chatWebSocketUrl(_roomId!),
      onConnected: () {
        if (mounted) setState(() => _wsConnected = true);
      },
      onDisconnected: () {
        if (mounted) setState(() => _wsConnected = false);
      },
      onEvent: (event) {
        if (event['type'] != null && event['type'] != 'message') return;
        if (event['body'] == null) return;
        final id = event['id']?.toString() ?? DateTime.now().millisecondsSinceEpoch.toString();
        if (!mounted) return;
        if (_messages.any((m) => m['id'] == id)) return;
        setState(() {
          _messages = [
            ..._messages,
            {
              'id': id,
              'body': event['body'],
              'sender_id': event['sender_id'] ?? 'unknown',
            },
          ];
        });
        if (_roomId != null) {
          _cache.saveMessages(_roomId!, _messages);
        }
      },
    );
    await _ws!.connect();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _roomId == null) return;

    final clientMessageId = DateTime.now().millisecondsSinceEpoch.toString();
    final localMessage = {
      'id': clientMessageId,
      'body': text,
      'created_at': DateTime.now().toIso8601String(),
      'sender_id': context.read<AuthService>().user?.id ?? 'local',
    };
    _controller.clear();
    setState(() => _messages = [..._messages, localMessage]);
    await _cache.saveMessages(_roomId!, _messages);

    _ws?.send({
      'type': 'message',
      'body': text,
      'client_message_id': clientMessageId,
    });

    try {
      final api = context.read<AuthService>().api;
      final sent = await api.sendChatMessage(_roomId!, text, clientMessageId: clientMessageId);
      if (mounted) {
        setState(() {
          _messages = [..._messages.where((m) => m['id'] != localMessage['id']), sent];
          _offline = false;
        });
        await _cache.saveMessages(_roomId!, _messages);
      }
    } catch (_) {
      if (mounted) setState(() => _offline = true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Column(
      children: [
        if (_offline)
          MaterialBanner(
            content: Text(l10n.chatOffline),
            leading: const Icon(Icons.cloud_off),
            actions: [
              TextButton(onPressed: _bootstrap, child: Text(l10n.retryButton)),
            ],
          ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          child: Text(
            _wsConnected ? l10n.chatWsConnected : l10n.chatWsReconnecting,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ),
        Expanded(
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : _messages.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.chat_bubble_outline, size: 64),
                          const SizedBox(height: 16),
                          Text(l10n.chatEmpty),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(12),
                      itemCount: _messages.length,
                      itemBuilder: (context, index) {
                        final msg = _messages[index];
                        return Align(
                          alignment: Alignment.centerLeft,
                          child: Card(
                            margin: const EdgeInsets.only(bottom: 8),
                            child: Padding(
                              padding: const EdgeInsets.all(12),
                              child: Text(msg['body']?.toString() ?? ''),
                            ),
                          ),
                        );
                      },
                    ),
        ),
        SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: InputDecoration(
                      hintText: l10n.chatInputHint,
                      border: const OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _send(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  onPressed: _send,
                  icon: const Icon(Icons.send),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
