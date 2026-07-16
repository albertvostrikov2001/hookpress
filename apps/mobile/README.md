# hook.press Mobile App (Stage 9)

Flutter client for iOS/Android with dev-login, feed, projects, chat stub, and audio player stub.

## Structure

- `lib/main.dart` — entry point
- `lib/app.dart` — routing and navigation shell
- `lib/screens/` — login, feed, projects, chat, player
- `lib/services/` — API client, auth, secure storage stub
- `lib/l10n/` — en/ru localizations

## Run

```bash
cd apps/mobile
flutter pub get
flutter analyze
flutter run
```

Default API: `http://localhost:8000/api/v1` (dev-login with `artist@example.com`).
