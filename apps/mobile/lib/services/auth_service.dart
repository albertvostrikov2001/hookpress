import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../models/user.dart';
import 'api_client.dart';
import 'secure_storage.dart';

const _tokenKey = 'hookpress_access_token';
const _refreshKey = 'hookpress_refresh_token';
const _userKey = 'hookpress_user';

class AuthService extends ChangeNotifier {
  AuthService({
    ApiClient? apiClient,
    SecureStorage? storage,
  })  : _api = apiClient ?? ApiClient(),
        _storage = storage ?? SecureStorageStub() {
    _api.onRefresh = _handleRefresh;
    _api.onUnauthorized = _handleUnauthorized;
  }

  final ApiClient _api;
  final SecureStorage _storage;

  User? _user;
  String? _accessToken;
  String? _refreshToken;

  User? get user => _user;
  String? get accessToken => _accessToken;
  String? get refreshToken => _refreshToken;
  ApiClient get api => _api;
  bool get isAuthenticated => _accessToken != null;

  Future<String?> _handleRefresh(String refreshToken) async {
    _refreshToken = refreshToken;
    _api.setRefreshToken(refreshToken);
    try {
      final body = await _api.refreshSession();
      final result = parseAuthResponse(body);
      _accessToken = result.tokens.accessToken;
      await _persistSession();
      notifyListeners();
      return _accessToken;
    } catch (_) {
      return null;
    }
  }

  Future<void> _handleUnauthorized() async {
    await logout();
  }

  Future<void> _persistSession() async {
    if (_accessToken != null) {
      await _storage.write(key: _tokenKey, value: _accessToken!);
    }
    if (_refreshToken != null) {
      await _storage.write(key: _refreshKey, value: _refreshToken!);
    }
    if (_user != null) {
      await _storage.write(
        key: _userKey,
        value: jsonEncode({
          'id': _user!.id,
          'email': _user!.email,
          'display_name': _user!.displayName,
          'roles': _user!.roles,
        }),
      );
    }
  }

  Future<void> restoreSession() async {
    _accessToken = await _storage.read(key: _tokenKey);
    _refreshToken = await _storage.read(key: _refreshKey);
    final userJson = await _storage.read(key: _userKey);
    if (_accessToken != null && userJson != null) {
      _api.setAccessToken(_accessToken);
      _api.setRefreshToken(_refreshToken);
      _user = User.fromJson(
        jsonDecode(userJson) as Map<String, dynamic>,
      );
      notifyListeners();
    }
  }

  Future<void> devLogin(String email) async {
    final body = await _api.devLogin(email);
    final result = parseAuthResponse(body);
    _accessToken = result.tokens.accessToken;
    _refreshToken = _api.refreshToken;
    _user = result.user;
    _api.setAccessToken(_accessToken);
    _api.setRefreshToken(_refreshToken);
    await _persistSession();
    notifyListeners();
  }

  Future<void> logout() async {
    _accessToken = null;
    _refreshToken = null;
    _user = null;
    _api.setAccessToken(null);
    _api.setRefreshToken(null);
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _refreshKey);
    await _storage.delete(key: _userKey);
    notifyListeners();
  }
}
