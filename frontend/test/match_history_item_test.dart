import 'package:fahman/features/match_setup/domain/match_snapshot.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('parses a match history item from the API response', () {
    final item = MatchHistoryItem.fromJson({
      'id': 'match-1',
      'status': 'completed',
      'created_at': '2026-09-06T10:00:00Z',
      'finished_at': '2026-09-06T10:30:00Z',
      'teams': [
        {'team_no': 1, 'name': 'الصقور', 'score': 2400},
        {'team_no': 2, 'name': 'النوابغ', 'score': 2200},
      ],
    });

    expect(item.status, 'completed');
    expect(item.teams[0].name, 'الصقور');
    expect(item.teams[1].score, 2200);
    expect(item.finishedAt, isNotNull);
  });
}
