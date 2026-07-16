import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

abstract class ChatMessageStore {
  Future<List<Map<String, dynamic>>> loadMessages(String roomId);
  Future<void> saveMessages(String roomId, List<Map<String, dynamic>> messages);
}

class ChatCache implements ChatMessageStore {
  ChatCache({SharedPreferences? prefs})
      : _prefsFuture = prefs != null
            ? Future.value(prefs)
            : SharedPreferences.getInstance();

  final Future<SharedPreferences> _prefsFuture;
  static const _prefix = 'chat_messages_';

  @override
  Future<List<Map<String, dynamic>>> loadMessages(String roomId) async {
    final prefs = await _prefsFuture;
    final raw = prefs.getString('$_prefix$roomId');
    if (raw == null) {
      return [];
    }
    try {
      final decoded = jsonDecode(raw);
      if (decoded is List) {
        return decoded.cast<Map<String, dynamic>>();
      }
    } catch (_) {
      return [];
    }
    return [];
  }

  @override
  Future<void> saveMessages(
    String roomId,
    List<Map<String, dynamic>> messages,
  ) async {
    final prefs = await _prefsFuture;
    await prefs.setString('$_prefix$roomId', jsonEncode(messages));
  }

  Future<void> appendMessage(
    String roomId,
    Map<String, dynamic> message,
  ) async {
    final existing = await loadMessages(roomId);
    existing.add(message);
    await saveMessages(roomId, existing);
  }

  Future<void> clearRoom(String roomId) async {
    final prefs = await _prefsFuture;
    await prefs.remove('$_prefix$roomId');
  }
}

class ChatCacheStub implements ChatMessageStore {
  final Map<String, List<Map<String, dynamic>>> _rooms = {};

  @override
  Future<List<Map<String, dynamic>>> loadMessages(String roomId) async {
    return List<Map<String, dynamic>>.from(_rooms[roomId] ?? const []);
  }

  @override
  Future<void> saveMessages(
    String roomId,
    List<Map<String, dynamic>> messages,
  ) async {
    _rooms[roomId] = List<Map<String, dynamic>>.from(messages);
  }
}
