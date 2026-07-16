import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

typedef ChatWsEventHandler = void Function(Map<String, dynamic> event);

/// WebSocket chat client with exponential backoff reconnect (Master Prompt §22.3).
class ChatWsService {
  ChatWsService({
    required this.wsUrl,
    this.onEvent,
    this.onConnected,
    this.onDisconnected,
  });

  final String wsUrl;
  final ChatWsEventHandler? onEvent;
  final VoidCallback? onConnected;
  final VoidCallback? onDisconnected;

  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  Timer? _reconnectTimer;
  int _retry = 0;
  bool _closed = false;

  static const _baseBackoffMs = 1000;
  static const _maxBackoffMs = 30000;

  bool get isConnected => _channel != null;

  Future<void> connect() async {
    _closed = false;
    await _open();
  }

  Future<void> _open() async {
    _reconnectTimer?.cancel();
    await _subscription?.cancel();
    await _channel?.sink.close();

    try {
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      _retry = 0;
      onConnected?.call();
      _subscription = _channel!.stream.listen(
        (raw) {
          try {
            final event = jsonDecode(raw as String) as Map<String, dynamic>;
            onEvent?.call(event);
          } catch (_) {
            /* ignore malformed payloads */
          }
        },
        onDone: _scheduleReconnect,
        onError: (_) => _scheduleReconnect(),
        cancelOnError: true,
      );
    } catch (_) {
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    if (_closed) return;
    onDisconnected?.call();
    _subscription?.cancel();
    _channel = null;
    final delayMs = (_baseBackoffMs * (1 << _retry.clamp(0, 5))).clamp(_baseBackoffMs, _maxBackoffMs);
    _retry += 1;
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(Duration(milliseconds: delayMs), () {
      if (!_closed) {
        unawaited(_open());
      }
    });
  }

  void send(Map<String, dynamic> payload) {
    final channel = _channel;
    if (channel == null) return;
    channel.sink.add(jsonEncode(payload));
  }

  Future<void> dispose() async {
    _closed = true;
    _reconnectTimer?.cancel();
    await _subscription?.cancel();
    await _channel?.sink.close();
    _channel = null;
  }
}
