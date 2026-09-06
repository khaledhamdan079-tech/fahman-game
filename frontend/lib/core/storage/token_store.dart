import 'dart:convert';
import 'dart:math';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SessionTokens {
  const SessionTokens({required this.accessToken, required this.refreshToken});

  final String accessToken;
  final String refreshToken;
}

class DeviceIdentity {
  const DeviceIdentity({required this.installationId, required this.secret});

  final String installationId;
  final String secret;
}

class TokenStore {
  TokenStore([FlutterSecureStorage? storage])
    : _storage = storage ?? const FlutterSecureStorage();

  static const _accessKey = 'fahman_access_token';
  static const _refreshKey = 'fahman_refresh_token';
  static const _installationIdKey = 'fahman_installation_id';
  static const _deviceSecretKey = 'fahman_device_secret';
  final FlutterSecureStorage _storage;

  Future<String?> readAccessToken() => _storage.read(key: _accessKey);

  Future<String?> readRefreshToken() => _storage.read(key: _refreshKey);

  Future<void> save(SessionTokens tokens) async {
    await Future.wait([
      _storage.write(key: _accessKey, value: tokens.accessToken),
      _storage.write(key: _refreshKey, value: tokens.refreshToken),
    ]);
  }

  Future<void> clear() async {
    await Future.wait([
      _storage.delete(key: _accessKey),
      _storage.delete(key: _refreshKey),
    ]);
  }

  Future<DeviceIdentity> readOrCreateDeviceIdentity() async {
    final stored = await Future.wait([
      _storage.read(key: _installationIdKey),
      _storage.read(key: _deviceSecretKey),
    ]);
    if (stored[0] != null && stored[1] != null) {
      return DeviceIdentity(installationId: stored[0]!, secret: stored[1]!);
    }

    final random = Random.secure();
    final uuidBytes = List<int>.generate(16, (_) => random.nextInt(256));
    uuidBytes[6] = (uuidBytes[6] & 0x0f) | 0x40;
    uuidBytes[8] = (uuidBytes[8] & 0x3f) | 0x80;
    final hex = uuidBytes
        .map((byte) => byte.toRadixString(16).padLeft(2, '0'))
        .join();
    final installationId =
        '${hex.substring(0, 8)}-${hex.substring(8, 12)}-'
        '${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
    final secretBytes = List<int>.generate(32, (_) => random.nextInt(256));
    final secret = base64UrlEncode(secretBytes).replaceAll('=', '');

    await Future.wait([
      _storage.write(key: _installationIdKey, value: installationId),
      _storage.write(key: _deviceSecretKey, value: secret),
    ]);
    return DeviceIdentity(installationId: installationId, secret: secret);
  }
}
