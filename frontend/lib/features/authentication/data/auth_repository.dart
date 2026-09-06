import 'package:dio/dio.dart';
import 'package:fahman/core/config/app_config.dart';
import 'package:fahman/core/network/api_client.dart';
import 'package:fahman/core/storage/token_store.dart';
import 'package:google_sign_in/google_sign_in.dart';

class UserProfile {
  const UserProfile({
    required this.id,
    required this.email,
    required this.displayName,
    this.avatarUrl,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
    id: json['id'] as String,
    email: json['email'] as String,
    displayName: json['display_name'] as String,
    avatarUrl: json['avatar_url'] as String?,
  );

  final String id;
  final String email;
  final String displayName;
  final String? avatarUrl;
}

class AuthRepository {
  AuthRepository(this._api, this._tokens);

  final ApiClient _api;
  final TokenStore _tokens;
  bool _googleInitialized = false;

  Future<UserProfile?> restoreSession() async {
    if (await _tokens.readAccessToken() == null) return null;
    try {
      final response = await _api.dio.get<Map<String, dynamic>>('/auth/me');
      return UserProfile.fromJson(response.data!);
    } on DioException {
      await _tokens.clear();
      return null;
    }
  }

  Future<UserProfile> signInWithGoogle() async {
    await _initializeGoogle();
    final google = GoogleSignIn.instance;
    if (!google.supportsAuthenticate()) {
      throw const AuthFailure(
        'تسجيل Google من داخل التطبيق متاح على Android وiOS حالياً.',
      );
    }
    final account = await google.authenticate();
    final idToken = account.authentication.idToken;
    if (idToken == null) {
      throw const AuthFailure('لم يرسل Google رمز الهوية. راجع إعدادات OAuth.');
    }
    final response = await _api.dio.post<Map<String, dynamic>>(
      '/auth/google',
      data: {'id_token': idToken},
    );
    final data = response.data!;
    await _tokens.save(
      SessionTokens(
        accessToken: data['access_token'] as String,
        refreshToken: data['refresh_token'] as String,
      ),
    );
    return UserProfile.fromJson(data['user'] as Map<String, dynamic>);
  }

  Future<void> signOut() async {
    await _initializeGoogle();
    await Future.wait([_tokens.clear(), GoogleSignIn.instance.signOut()]);
  }

  Future<void> _initializeGoogle() async {
    if (_googleInitialized) return;
    await GoogleSignIn.instance.initialize(
      clientId: AppConfig.googleClientId.isEmpty
          ? null
          : AppConfig.googleClientId,
      serverClientId: AppConfig.googleServerClientId.isEmpty
          ? null
          : AppConfig.googleServerClientId,
    );
    _googleInitialized = true;
  }
}

class AuthFailure implements Exception {
  const AuthFailure(this.message);
  final String message;
}
