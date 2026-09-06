import 'package:fahman/features/match_setup/domain/category_availability.dart';
import 'package:fahman/features/match_setup/domain/match_snapshot.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('parses backend category availability', () {
    final category = CategoryAvailability.fromJson({
      'id': '0d9030c4-b024-4c04-a162-b6d920b190bb',
      'name_ar': 'عالم السيارات',
      'description_ar': 'أصوات ومحركات',
      'unused_200': 6,
      'unused_400': 4,
      'unused_600': 2,
      'complete_matches_possible': 1,
      'eligible': true,
    });

    expect(category.name, 'عالم السيارات');
    expect(category.totalUnused, 12);
    expect(category.completeMatches, 1);
    expect(category.eligible, isTrue);
  });

  test('demo match has six correctly tiered questions per category', () {
    final match = MatchSnapshot.demo(
      categories: const [
        CategoryAvailabilityReference(id: 'cars', name: 'السيارات'),
      ],
      teamOne: 'الصقور',
      teamTwo: 'الأبطال',
    );

    final questions = match.categories.single.questions;
    expect(questions, hasLength(6));
    expect(questions.map((item) => item.points), [
      200,
      200,
      400,
      400,
      600,
      600,
    ]);
  });

  test(
    'parses an active multimedia question without leaking option metadata',
    () {
      final match = MatchSnapshot.fromJson({
        'id': 'match-1',
        'status': 'active',
        'current_team_no': 1,
        'timer_seconds': 60,
        'version': 2,
        'teams': [
          {'team_no': 1, 'name': 'أ', 'score': 0},
          {'team_no': 2, 'name': 'ب', 'score': 0},
        ],
        'categories': <dynamic>[],
        'lifelines': <dynamic>[],
        'active_question': {
          'id': 'question-1',
          'question_type': 'audio',
          'prompt_ar': 'لمن هذا الصوت؟',
          'options': [
            {'text_ar': 'الخيار الأول', 'sort_order': 0},
          ],
          'answer_ar': null,
          'points': 400,
          'effective_points': 400,
          'state': 'open',
          'media_asset_id': 'media-1',
          'deadline_at': null,
          'play_count': 0,
          'max_plays': 2,
          'choosing_team_no': 1,
        },
      });

      expect(match.activeQuestion?.type, 'audio');
      expect(match.activeQuestion?.options, ['الخيار الأول']);
      expect(match.activeQuestion?.answer, isNull);
    },
  );
}
