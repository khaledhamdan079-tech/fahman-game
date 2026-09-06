import 'package:fahman/core/storage/token_store.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'installation identity is generated once and survives token clearing',
    () async {
      FlutterSecureStorage.setMockInitialValues({});
      final store = TokenStore();

      final first = await store.readOrCreateDeviceIdentity();
      await store.save(
        const SessionTokens(accessToken: 'access', refreshToken: 'refresh'),
      );
      await store.clear();
      final restored = await store.readOrCreateDeviceIdentity();

      expect(
        first.installationId,
        matches(
          RegExp(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
          ),
        ),
      );
      expect(first.secret.length, greaterThanOrEqualTo(43));
      expect(restored.installationId, first.installationId);
      expect(restored.secret, first.secret);
      expect(await store.readAccessToken(), isNull);
      expect(await store.readRefreshToken(), isNull);
    },
  );
}
