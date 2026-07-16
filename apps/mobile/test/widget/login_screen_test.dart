import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';

import 'package:hookpress_mobile/l10n/app_localizations.dart';
import 'package:hookpress_mobile/screens/login_screen.dart';
import 'package:hookpress_mobile/services/api_client.dart';
import 'package:hookpress_mobile/services/auth_service.dart';
import 'package:hookpress_mobile/services/secure_storage.dart';

class _FakeHttpClient implements http.Client {
  @override
  noSuchMethod(Invocation invocation) => throw UnimplementedError();
}

class _FakeApiClient extends ApiClient {
  _FakeApiClient() : super(client: _FakeHttpClient());

  @override
  Future<Map<String, dynamic>> devLogin(String email) async {
    return {
      'tokens': {'access_token': 'test-token', 'expires_in': 900},
      'user': {
        'id': '00000000-0000-0000-0000-000000000001',
        'email': email,
        'display_name': 'Test User',
        'roles': ['artist'],
      },
    };
  }
}

class _FailingApiClient extends ApiClient {
  _FailingApiClient() : super(client: _FakeHttpClient());

  @override
  Future<Map<String, dynamic>> devLogin(String email) async {
    throw ApiException(500, 'server error');
  }
}

void main() {
  Widget buildApp({required AuthService auth}) {
    return ChangeNotifierProvider<AuthService>.value(
      value: auth,
      child: MaterialApp(
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('en'),
        home: const LoginScreen(),
      ),
    );
  }

  testWidgets('login screen shows email field and button', (tester) async {
    final auth = AuthService(
      apiClient: _FakeApiClient(),
      storage: SecureStorageStub(),
    );
    await tester.pumpWidget(buildApp(auth: auth));

    expect(find.text('Sign in'), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
    expect(find.text('Dev login'), findsOneWidget);
  });

  testWidgets('login submits email via auth service', (tester) async {
    final auth = AuthService(
      apiClient: _FakeApiClient(),
      storage: SecureStorageStub(),
    );
    await tester.pumpWidget(buildApp(auth: auth));

    await tester.enterText(find.byType(TextField), 'artist@example.com');
    await tester.tap(find.text('Dev login'));
    await tester.pumpAndSettle();

    expect(auth.isAuthenticated, isTrue);
    expect(auth.user?.email, 'artist@example.com');
  });

  testWidgets('login shows error message on failure', (tester) async {
    final auth = AuthService(
      apiClient: _FailingApiClient(),
      storage: SecureStorageStub(),
    );
    await tester.pumpWidget(buildApp(auth: auth));

    await tester.tap(find.text('Dev login'));
    await tester.pumpAndSettle();

    expect(find.text('Login failed'), findsOneWidget);
    expect(auth.isAuthenticated, isFalse);
  });
}
