import 'package:flutter/foundation.dart';

import 'package:flutter/widgets.dart';



class AppLocalizations {

  AppLocalizations(this.locale);



  final Locale locale;



  static AppLocalizations? of(BuildContext context) {

    return Localizations.of<AppLocalizations>(context, AppLocalizations);

  }



  static const LocalizationsDelegate<AppLocalizations> delegate =

      _AppLocalizationsDelegate();



  static const List<Locale> supportedLocales = [

    Locale('en'),

    Locale('ru'),

  ];



  static final Map<String, Map<String, String>> _localizedValues = {

    'en': {

      'appTitle': 'hook.press',

      'loginTitle': 'Sign in',

      'emailLabel': 'Email',

      'loginButton': 'Dev login',

      'feedTitle': 'Feed',

      'projectsTitle': 'Projects',

      'chatTitle': 'Chat',

      'playerTitle': 'Player',

      'profileTitle': 'Profile',

      'logoutButton': 'Log out',

      'feedEmpty': 'No articles yet',

      'feedLoadError': 'Could not load feed',

      'projectsEmpty': 'No projects yet',

      'chatStub': 'Chat coming soon',

      'chatEmpty': 'No messages yet',

      'chatOffline': 'Offline — showing cached messages',

      'chatInputHint': 'Type a message',

      'chatWsConnected': 'WebSocket connected',

      'chatWsReconnecting': 'WebSocket reconnecting…',

      'retryButton': 'Retry',

      'playerStub': 'Audio player stub',

      'playerTrackTitle': 'Demo Track',

      'playerArtist': 'hook.press artist',

      'playerSourceLabel': 'Media asset {assetId}',

      'profileRoles': 'Roles',

      'profileNoRoles': 'No roles',

      'profileSession': 'Session',

      'profileSessionActive': 'Refresh token stored',

      'profileSessionMissing': 'Access token only',

      'loginError': 'Login failed',

    },

    'ru': {

      'appTitle': 'hook.press',

      'loginTitle': 'Вход',

      'emailLabel': 'Email',

      'loginButton': 'Dev вход',

      'feedTitle': 'Лента',

      'projectsTitle': 'Проекты',

      'chatTitle': 'Чат',

      'playerTitle': 'Плеер',

      'profileTitle': 'Профиль',

      'logoutButton': 'Выйти',

      'feedEmpty': 'Пока нет статей',

      'feedLoadError': 'Не удалось загрузить ленту',

      'projectsEmpty': 'Пока нет проектов',

      'chatStub': 'Чат скоро будет',

      'chatEmpty': 'Пока нет сообщений',

      'chatOffline': 'Офлайн — показаны кэшированные сообщения',

      'chatInputHint': 'Введите сообщение',

      'chatWsConnected': 'WebSocket подключён',

      'chatWsReconnecting': 'WebSocket переподключается…',

      'retryButton': 'Повторить',

      'playerStub': 'Заглушка аудиоплеера',

      'playerTrackTitle': 'Демо трек',

      'playerArtist': 'hook.press артист',

      'playerSourceLabel': 'Медиа-файл {assetId}',

      'profileRoles': 'Роли',

      'profileNoRoles': 'Нет ролей',

      'profileSession': 'Сессия',

      'profileSessionActive': 'Refresh-токен сохранён',

      'profileSessionMissing': 'Только access-токен',

      'loginError': 'Ошибка входа',

    },

  };



  String _t(String key) =>

      _localizedValues[locale.languageCode]?[key] ??

      _localizedValues['en']![key]!;



  String get appTitle => _t('appTitle');

  String get loginTitle => _t('loginTitle');

  String get emailLabel => _t('emailLabel');

  String get loginButton => _t('loginButton');

  String get feedTitle => _t('feedTitle');

  String get projectsTitle => _t('projectsTitle');

  String get chatTitle => _t('chatTitle');

  String get playerTitle => _t('playerTitle');

  String get profileTitle => _t('profileTitle');

  String get logoutButton => _t('logoutButton');

  String get feedEmpty => _t('feedEmpty');

  String get feedLoadError => _t('feedLoadError');

  String get projectsEmpty => _t('projectsEmpty');

  String get chatStub => _t('chatStub');

  String get chatEmpty => _t('chatEmpty');

  String get chatOffline => _t('chatOffline');

  String get chatInputHint => _t('chatInputHint');

  String get chatWsConnected => _t('chatWsConnected');

  String get chatWsReconnecting => _t('chatWsReconnecting');

  String get retryButton => _t('retryButton');

  String get playerStub => _t('playerStub');

  String get playerTrackTitle => _t('playerTrackTitle');

  String get playerArtist => _t('playerArtist');

  String playerSourceLabel(String assetId) =>
      _t('playerSourceLabel').replaceAll('{assetId}', assetId);

  String get profileRoles => _t('profileRoles');

  String get profileNoRoles => _t('profileNoRoles');

  String get profileSession => _t('profileSession');

  String get profileSessionActive => _t('profileSessionActive');

  String get profileSessionMissing => _t('profileSessionMissing');

  String get loginError => _t('loginError');

}



class _AppLocalizationsDelegate

    extends LocalizationsDelegate<AppLocalizations> {

  const _AppLocalizationsDelegate();



  @override

  bool isSupported(Locale locale) =>

      ['en', 'ru'].contains(locale.languageCode);



  @override

  Future<AppLocalizations> load(Locale locale) {

    return SynchronousFuture<AppLocalizations>(AppLocalizations(locale));

  }



  @override

  bool shouldReload(_AppLocalizationsDelegate old) => false;

}

