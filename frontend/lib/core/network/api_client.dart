import 'package:dio/dio.dart';
import 'package:fahman/core/config/app_config.dart';
import 'package:fahman/core/storage/token_store.dart';

class ApiClient {
  ApiClient(this._tokens)
    : dio = Dio(
        BaseOptions(
          baseUrl: AppConfig.apiBaseUrl,
          connectTimeout: const Duration(seconds: 12),
          receiveTimeout: const Duration(seconds: 20),
          headers: const {'Accept': 'application/json'},
        ),
      ) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _tokens.readAccessToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          final request = error.requestOptions;
          final shouldRefresh =
              error.response?.statusCode == 401 &&
              request.extra['retried_after_refresh'] != true &&
              !request.path.endsWith('/auth/google') &&
              !request.path.endsWith('/auth/device/session') &&
              !request.path.endsWith('/auth/refresh');
          if (!shouldRefresh) {
            handler.next(error);
            return;
          }
          final accessToken = await _refreshAccessToken();
          if (accessToken == null) {
            handler.next(error);
            return;
          }
          request.headers['Authorization'] = 'Bearer $accessToken';
          request.extra['retried_after_refresh'] = true;
          try {
            handler.resolve(await dio.fetch<dynamic>(request));
          } on DioException catch (retryError) {
            handler.next(retryError);
          }
        },
      ),
    );
  }

  final TokenStore _tokens;
  final Dio dio;
  Future<String?>? _refreshing;

  Future<String?> _refreshAccessToken() {
    final activeRefresh = _refreshing;
    if (activeRefresh != null) return activeRefresh;
    final operation = _performRefresh();
    _refreshing = operation;
    return operation.whenComplete(() => _refreshing = null);
  }

  Future<String?> _performRefresh() async {
    final refreshToken = await _tokens.readRefreshToken();
    if (refreshToken == null) return null;
    try {
      final refreshClient = Dio(BaseOptions(baseUrl: AppConfig.apiBaseUrl));
      final response = await refreshClient.post<Map<String, dynamic>>(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      final data = response.data!;
      final accessToken = data['access_token'] as String;
      await _tokens.save(
        SessionTokens(
          accessToken: accessToken,
          refreshToken: data['refresh_token'] as String,
        ),
      );
      return accessToken;
    } on DioException {
      await _tokens.clear();
      return null;
    }
  }
}
