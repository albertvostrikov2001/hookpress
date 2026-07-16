import 'dart:convert';



import 'package:http/http.dart' as http;



import '../models/user.dart';



typedef RefreshHandler = Future<String?> Function(String refreshToken);

typedef UnauthorizedHandler = Future<void> Function();



class ApiClient {

  ApiClient({

    this.baseUrl = 'http://localhost:8000/api/v1',

    http.Client? client,

  }) : _client = client ?? http.Client();



  final String baseUrl;

  final http.Client _client;



  String? _accessToken;

  String? _refreshToken;

  RefreshHandler? onRefresh;

  UnauthorizedHandler? onUnauthorized;



  void setAccessToken(String? token) => _accessToken = token;

  void setRefreshToken(String? token) => _refreshToken = token;

  String? get accessToken => _accessToken;

  String? get refreshToken => _refreshToken;



  Map<String, String> _headers({bool json = true}) {

    final headers = <String, String>{};

    if (json) {

      headers['Content-Type'] = 'application/json';

    }

    if (_accessToken != null) {

      headers['Authorization'] = 'Bearer $_accessToken';

    }

    return headers;

  }



  String? _extractRefreshCookie(http.Response resp) {

    final raw = resp.headers['set-cookie'];

    if (raw == null) {

      return null;

    }

    final match = RegExp(r'hookpress_refresh=([^;]+)').firstMatch(raw);

    return match?.group(1);

  }



  void _captureRefreshCookie(http.Response resp) {

    final token = _extractRefreshCookie(resp);

    if (token != null) {

      _refreshToken = token;

    }

  }



  Future<http.Response> _send(

    Future<http.Response> Function() request, {

    bool retryOn401 = true,

  }) async {

    var resp = await request();

    if (resp.statusCode == 401 && retryOn401 && _refreshToken != null) {

      final refreshed = await _tryRefresh();

      if (refreshed) {

        resp = await request();

      } else {

        await onUnauthorized?.call();

      }

    }

    return resp;

  }



  Future<bool> _tryRefresh() async {

    if (_refreshToken == null) {

      return false;

    }

    if (onRefresh != null) {

      final newAccess = await onRefresh!(_refreshToken!);

      if (newAccess == null) {

        return false;

      }

      _accessToken = newAccess;

      return true;

    }

    final resp = await _client.post(

      Uri.parse('$baseUrl/auth/refresh'),

      headers: {

        'Authorization': 'Bearer $_refreshToken',

        'Content-Type': 'application/json',

      },

    );

    if (resp.statusCode >= 400) {

      return false;

    }

    final body = jsonDecode(resp.body) as Map<String, dynamic>;

    final tokens = body['tokens'] as Map<String, dynamic>;

    _accessToken = tokens['access_token'] as String;

    _captureRefreshCookie(resp);

    return true;

  }



  Future<Map<String, dynamic>> devLogin(String email) async {

    final resp = await _client.post(

      Uri.parse('$baseUrl/auth/dev-login'),

      headers: _headers(),

      body: jsonEncode({'email': email}),

    );

    if (resp.statusCode >= 400) {

      throw ApiException(resp.statusCode, resp.body);

    }

    final body = jsonDecode(resp.body) as Map<String, dynamic>;

    final tokens = body['tokens'] as Map<String, dynamic>;

    _accessToken = tokens['access_token'] as String;

    _captureRefreshCookie(resp);

    return body;

  }



  Future<Map<String, dynamic>> refreshSession() async {

    if (_refreshToken == null) {

      throw ApiException(401, 'No refresh token');

    }

    final resp = await _client.post(

      Uri.parse('$baseUrl/auth/refresh'),

      headers: {

        'Authorization': 'Bearer $_refreshToken',

        'Content-Type': 'application/json',

      },

    );

    if (resp.statusCode >= 400) {

      throw ApiException(resp.statusCode, resp.body);

    }

    final body = jsonDecode(resp.body) as Map<String, dynamic>;

    final tokens = body['tokens'] as Map<String, dynamic>;

    _accessToken = tokens['access_token'] as String;

    _captureRefreshCookie(resp);

    return body;

  }



  Future<List<Map<String, dynamic>>> listFeedArticles({int limit = 20}) async {

    final resp = await _send(

      () => _client.get(

        Uri.parse('$baseUrl/feed/articles?limit=$limit'),

        headers: _headers(json: false),

      ),

    );

    if (resp.statusCode >= 400) {

      throw ApiException(resp.statusCode, resp.body);

    }

    final body = jsonDecode(resp.body);

    if (body is List) {

      return body.cast<Map<String, dynamic>>();

    }

    return [];

  }



  Future<List<Map<String, dynamic>>> listStudioProjects() async {

    final resp = await _send(

      () => _client.get(

        Uri.parse('$baseUrl/studio/projects'),

        headers: _headers(json: false),

      ),

    );

    if (resp.statusCode == 404 || resp.statusCode == 405) {

      return [];

    }

    if (resp.statusCode >= 400) {

      throw ApiException(resp.statusCode, resp.body);

    }

    final body = jsonDecode(resp.body);

    if (body is List) {

      return body.cast<Map<String, dynamic>>();

    }

    if (body is Map && body['items'] is List) {

      return (body['items'] as List).cast<Map<String, dynamic>>();

    }

    return [];

  }



  Future<Map<String, dynamic>> createStudioProject(String title) async {

    final resp = await _send(

      () => _client.post(

        Uri.parse('$baseUrl/studio/projects'),

        headers: _headers(),

        body: jsonEncode({'title': title}),

      ),

    );

    if (resp.statusCode >= 400) {

      throw ApiException(resp.statusCode, resp.body);

    }

    return jsonDecode(resp.body) as Map<String, dynamic>;

  }



  Future<Map<String, dynamic>> createChatRoom({String name = 'Mobile room'}) async {

    final resp = await _send(

      () => _client.post(

        Uri.parse('$baseUrl/chat/rooms'),

        headers: _headers(),

        body: jsonEncode({'name': name, 'member_ids': []}),

      ),

    );

    if (resp.statusCode >= 400) {

      throw ApiException(resp.statusCode, resp.body);

    }

    return jsonDecode(resp.body) as Map<String, dynamic>;

  }



  String chatWebSocketUrl(String roomId) {

    final wsBase = baseUrl

        .replaceFirst('https://', 'wss://')

        .replaceFirst('http://', 'ws://')

        .replaceFirst('/api/v1', '');

    final token = _accessToken ?? '';

    return '$wsBase/api/v1/ws/chat/$roomId?token=$token';

  }



  Future<Map<String, dynamic>?> getAudioPresignedUrl(String projectId) async {

    final resp = await _send(

      () => _client.get(

        Uri.parse('$baseUrl/studio/projects/$projectId/audio/presigned-url'),

        headers: _headers(json: false),

      ),

    );

    if (resp.statusCode == 404) {

      return null;

    }

    if (resp.statusCode >= 400) {

      throw ApiException(resp.statusCode, resp.body);

    }

    return jsonDecode(resp.body) as Map<String, dynamic>;

  }



  Future<List<Map<String, dynamic>>> listChatMessages(String roomId) async {

    final resp = await _send(

      () => _client.get(

        Uri.parse('$baseUrl/chat/rooms/$roomId/messages'),

        headers: _headers(json: false),

      ),

    );

    if (resp.statusCode == 404) {

      return [];

    }

    if (resp.statusCode >= 400) {

      throw ApiException(resp.statusCode, resp.body);

    }

    final body = jsonDecode(resp.body) as Map<String, dynamic>;

    final items = body['items'];

    if (items is List) {

      return items.cast<Map<String, dynamic>>();

    }

    return [];

  }



  Future<Map<String, dynamic>> sendChatMessage(

    String roomId,

    String text, {

    String? clientMessageId,

  }) async {

    final resp = await _send(

      () => _client.post(

        Uri.parse('$baseUrl/chat/rooms/$roomId/messages'),

        headers: _headers(),

        body: jsonEncode({

          'body': text,

          'client_message_id': clientMessageId ?? DateTime.now().millisecondsSinceEpoch.toString(),

        }),

      ),

    );

    if (resp.statusCode >= 400) {

      throw ApiException(resp.statusCode, resp.body);

    }

    return jsonDecode(resp.body) as Map<String, dynamic>;

  }

}



class ApiException implements Exception {

  ApiException(this.statusCode, this.body);

  final int statusCode;

  final String body;



  @override

  String toString() => 'ApiException($statusCode): $body';

}



typedef AuthResult = ({AuthTokens tokens, User user});



AuthResult parseAuthResponse(Map<String, dynamic> json) {

  final tokens = AuthTokens.fromJson(json['tokens'] as Map<String, dynamic>);

  final user = User.fromJson(json['user'] as Map<String, dynamic>);

  return (tokens: tokens, user: user);

}

