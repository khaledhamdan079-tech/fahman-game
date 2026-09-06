import 'package:dio/dio.dart';
import 'package:fahman/core/network/api_client.dart';
import 'package:fahman/core/storage/token_store.dart';
import 'package:flutter/foundation.dart';

class UserProfile {
  const UserProfile({
    required this.id,
    this.email,
    required this.displayName,
    this.avatarUrl,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
    id: json['id'] as String,
    email: json['email'] as String?,
    displayName: json['display_name'] as String,
    avatarUrl: json['avatar_url'] as String?,
  );

  final String id;
  final String? email;
  final String displayName;
  final String? avatarUrl;
}

class AuthRepository {
  AuthRepository(this._api, this._tokens);

  final ApiClient _api;
  final TokenStore _tokens;
  Future<UserProfile> establishDeviceSession() async {
    final identity = await _tokens.readOrCreateDeviceIdentity();
    final payload = {
      'installation_id': identity.installationId,
      'device_secret': identity.secret,
      'platform': defaultTargetPlatform.name,
      'display_name': 'لاعب فهمان',
    };

    if (await _tokens.readAccessToken() != null) {
      UserProfile? restoredUser;
      try {
        final response = await _api.dio.get<Map<String, dynamic>>('/auth/me');
        restoredUser = UserProfile.fromJson(response.data!);
      } on DioException {
        // The refresh interceptor has already tried to recover the old session.
      }
      if (restoredUser != null) {
        // A valid token from the Google version is attached once to this
        // installation, preserving match history and used questions.
        try {
          await _api.dio.post<Map<String, dynamic>>(
            '/auth/device/attach',
            data: payload,
          );
        } on DioException catch (error) {
          if (error.response?.statusCode != 409) rethrow;
        }
        return restoredUser;
      }
    }

    final response = await _api.dio.post<Map<String, dynamic>>(
      '/auth/device/session',
      data: payload,
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
    await _tokens.clear();
  }
}

class AuthFailure implements Exception {
  const AuthFailure(this.message);
  final String message;
}
