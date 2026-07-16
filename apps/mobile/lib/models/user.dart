class User {
  const User({
    required this.id,
    required this.email,
    required this.displayName,
    required this.roles,
  });

  final String id;
  final String email;
  final String displayName;
  final List<String> roles;

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String,
      email: json['email'] as String,
      displayName: json['display_name'] as String? ?? '',
      roles: (json['roles'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(),
    );
  }
}

class AuthTokens {
  const AuthTokens({required this.accessToken, required this.expiresIn});

  final String accessToken;
  final int expiresIn;

  factory AuthTokens.fromJson(Map<String, dynamic> json) {
    return AuthTokens(
      accessToken: json['access_token'] as String,
      expiresIn: json['expires_in'] as int? ?? 900,
    );
  }
}
