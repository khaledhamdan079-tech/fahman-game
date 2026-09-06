import 'package:fahman/core/network/api_client.dart';
import 'package:fahman/core/storage/token_store.dart';
import 'package:fahman/features/authentication/data/auth_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final tokenStoreProvider = Provider<TokenStore>((ref) => TokenStore());

final apiClientProvider = Provider<ApiClient>(
  (ref) => ApiClient(ref.watch(tokenStoreProvider)),
);

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(
    ref.watch(apiClientProvider),
    ref.watch(tokenStoreProvider),
  ),
);

enum AuthStatus { booting, signedOut, busy, signedIn, demo, error }

class AuthState {
  const AuthState({required this.status, this.user, this.message});

  const AuthState.booting() : this(status: AuthStatus.booting);

  final AuthStatus status;
  final UserProfile? user;
  final String? message;

  bool get hasAccess =>
      status == AuthStatus.signedIn || status == AuthStatus.demo;
  bool get isDemo => status == AuthStatus.demo;
}

final authControllerProvider = NotifierProvider<AuthController, AuthState>(
  AuthController.new,
);

class AuthController extends Notifier<AuthState> {
  bool _didBootstrap = false;

  AuthRepository get _repository => ref.read(authRepositoryProvider);

  @override
  AuthState build() => const AuthState.booting();

  Future<void> bootstrap() async {
    if (_didBootstrap) return;
    _didBootstrap = true;
    final user = await _repository.restoreSession();
    state = AuthState(
      status: user == null ? AuthStatus.signedOut : AuthStatus.signedIn,
      user: user,
    );
  }

  Future<bool> signIn() async {
    state = const AuthState(status: AuthStatus.busy);
    try {
      final user = await _repository.signInWithGoogle();
      state = AuthState(status: AuthStatus.signedIn, user: user);
      return true;
    } on AuthFailure catch (error) {
      state = AuthState(status: AuthStatus.error, message: error.message);
    } catch (_) {
      state = const AuthState(
        status: AuthStatus.error,
        message: 'تعذر تسجيل الدخول. تأكد من الاتصال وإعدادات Google.',
      );
    }
    return false;
  }

  void continueAsDemo() {
    state = const AuthState(
      status: AuthStatus.demo,
      user: UserProfile(
        id: 'demo',
        email: 'demo@fahman.local',
        displayName: 'ضيف فهمان',
      ),
    );
  }

  Future<void> signOut() async {
    if (!state.isDemo) await _repository.signOut();
    state = const AuthState(status: AuthStatus.signedOut);
  }
}
