import 'package:dio/dio.dart';
import 'package:fahman/core/network/api_client.dart';
import 'package:fahman/features/match_setup/domain/category_availability.dart';
import 'package:fahman/features/match_setup/domain/match_snapshot.dart';

class GameRepository {
  const GameRepository(this._api);

  final ApiClient _api;

  Future<List<CategoryAvailability>> fetchCategories() async {
    final response = await _api.dio.get<List<dynamic>>('/categories/eligible');
    return response.data!
        .map(
          (item) => CategoryAvailability.fromJson(item as Map<String, dynamic>),
        )
        .toList();
  }

  Future<MatchSnapshot?> fetchActiveMatch() async {
    final response = await _api.dio.get<Map<String, dynamic>?>(
      '/matches/active',
    );
    final data = response.data;
    return data == null ? null : MatchSnapshot.fromJson(data);
  }

  Future<MatchSnapshot> fetchMatch(String matchId) async {
    final response = await _api.dio.get<Map<String, dynamic>>(
      '/matches/$matchId',
    );
    return MatchSnapshot.fromJson(response.data!);
  }

  Future<List<MatchHistoryItem>> fetchHistory() async {
    final response = await _api.dio.get<Map<String, dynamic>>('/matches');
    return (response.data!['items'] as List<dynamic>)
        .map((item) => MatchHistoryItem.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<MatchSnapshot> createMatch({
    required List<CategoryAvailability> categories,
    required String teamOne,
    required String teamTwo,
  }) async {
    final idempotencyKey = 'flutter-${DateTime.now().microsecondsSinceEpoch}';
    final response = await _api.dio.post<Map<String, dynamic>>(
      '/matches',
      options: Options(headers: {'Idempotency-Key': idempotencyKey}),
      data: {
        'category_ids': categories.map((item) => item.id).toList(),
        'team_one_name': teamOne,
        'team_two_name': teamTwo,
        'timer_seconds': 60,
      },
    );
    return MatchSnapshot.fromJson(response.data!);
  }

  Future<MatchSnapshot> openQuestion(MatchSnapshot match, String questionId) =>
      _command(
        '/matches/${match.id}/questions/$questionId/open',
        match.version,
      );

  Future<MatchSnapshot> armLifeline(
    MatchSnapshot match,
    String type,
    String questionId,
  ) => _command(
    '/matches/${match.id}/lifelines/$type/arm',
    match.version,
    extraData: {'match_question_id': questionId},
  );

  Future<MatchSnapshot> markMediaReady(MatchSnapshot match) => _command(
    '/matches/${match.id}/questions/${match.activeQuestion!.id}/media-ready',
    match.version,
  );

  Future<MatchSnapshot> recordMediaPlay(MatchSnapshot match) => _command(
    '/matches/${match.id}/questions/${match.activeQuestion!.id}/play',
    match.version,
  );

  Future<MatchSnapshot> revealQuestion(MatchSnapshot match) => _command(
    '/matches/${match.id}/questions/${match.activeQuestion!.id}/reveal',
    match.version,
  );

  Future<MatchSnapshot> scoreQuestion(
    MatchSnapshot match,
    int? answeredByTeam,
  ) => _command(
    '/matches/${match.id}/questions/${match.activeQuestion!.id}/score',
    match.version,
    extraData: {'answered_by_team_no': answeredByTeam},
  );

  Future<MediaPlaybackSnapshot> fetchPlayback(
    String matchId,
    String mediaAssetId,
  ) async {
    final response = await _api.dio.get<Map<String, dynamic>>(
      '/matches/$matchId/media/$mediaAssetId/playback',
    );
    return MediaPlaybackSnapshot.fromJson(response.data!);
  }

  Future<MatchSnapshot> _command(
    String path,
    int expectedVersion, {
    Map<String, dynamic> extraData = const {},
  }) async {
    final response = await _api.dio.post<Map<String, dynamic>>(
      path,
      options: Options(
        headers: {
          'Idempotency-Key': 'flutter-${DateTime.now().microsecondsSinceEpoch}',
        },
      ),
      data: {'expected_version': expectedVersion, ...extraData},
    );
    return MatchSnapshot.fromJson(response.data!);
  }
}
