import 'dart:math';

import 'package:fahman/features/authentication/presentation/auth_controller.dart';
import 'package:fahman/features/match_setup/data/game_repository.dart';
import 'package:fahman/features/match_setup/domain/category_availability.dart';
import 'package:fahman/features/match_setup/domain/match_snapshot.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final gameRepositoryProvider = Provider<GameRepository>(
  (ref) => GameRepository(ref.watch(apiClientProvider)),
);

const demoCategories = [
  CategoryAvailability(
    id: 'demo-history',
    name: 'تاريخنا',
    description: 'شخصيات وأحداث صنعت الحكاية',
    unused200: 14,
    unused400: 12,
    unused600: 10,
    completeMatches: 5,
    eligible: true,
  ),
  CategoryAvailability(
    id: 'demo-cinema',
    name: 'سينما وشاشة',
    description: 'مشاهد خالدة وأصوات لا تُنسى',
    unused200: 18,
    unused400: 16,
    unused600: 12,
    completeMatches: 6,
    eligible: true,
  ),
  CategoryAvailability(
    id: 'demo-cars',
    name: 'عالم السيارات',
    description: 'شعارات ومحركات وطرقات',
    unused200: 12,
    unused400: 10,
    unused600: 8,
    completeMatches: 4,
    eligible: true,
  ),
  CategoryAvailability(
    id: 'demo-sports',
    name: 'رياضة',
    description: 'ملاعب وأبطال ولحظات حاسمة',
    unused200: 20,
    unused400: 18,
    unused600: 14,
    completeMatches: 7,
    eligible: true,
  ),
  CategoryAvailability(
    id: 'demo-geography',
    name: 'حول العالم',
    description: 'مدن وأعلام ومعالم',
    unused200: 16,
    unused400: 14,
    unused600: 12,
    completeMatches: 6,
    eligible: true,
  ),
  CategoryAvailability(
    id: 'demo-science',
    name: 'علوم واختراعات',
    description: 'تجارب وأفكار غيرت حياتنا',
    unused200: 12,
    unused400: 12,
    unused600: 10,
    completeMatches: 5,
    eligible: true,
  ),
  CategoryAvailability(
    id: 'demo-food',
    name: 'على السفرة',
    description: 'نكهات وأطباق من كل مكان',
    unused200: 10,
    unused400: 10,
    unused600: 8,
    completeMatches: 4,
    eligible: true,
  ),
  CategoryAvailability(
    id: 'demo-music',
    name: 'نغمة وكلمة',
    description: 'أغانٍ وأصوات وفنانون',
    unused200: 16,
    unused400: 12,
    unused600: 10,
    completeMatches: 5,
    eligible: true,
  ),
];

final categoriesProvider = FutureProvider<List<CategoryAvailability>>((ref) {
  if (ref.watch(authControllerProvider).isDemo) {
    return Future.value(demoCategories);
  }
  return ref.watch(gameRepositoryProvider).fetchCategories();
});

class SetupState {
  const SetupState({
    this.categoryCount = 3,
    this.selected = const {},
    this.isCreating = false,
    this.error,
    this.activeMatch,
  });

  final int categoryCount;
  final Set<String> selected;
  final bool isCreating;
  final String? error;
  final MatchSnapshot? activeMatch;

  SetupState copyWith({
    int? categoryCount,
    Set<String>? selected,
    bool? isCreating,
    String? error,
    bool clearError = false,
    MatchSnapshot? activeMatch,
    bool clearActiveMatch = false,
  }) => SetupState(
    categoryCount: categoryCount ?? this.categoryCount,
    selected: selected ?? this.selected,
    isCreating: isCreating ?? this.isCreating,
    error: clearError ? null : error ?? this.error,
    activeMatch: clearActiveMatch ? null : activeMatch ?? this.activeMatch,
  );
}

final setupControllerProvider = NotifierProvider<SetupController, SetupState>(
  SetupController.new,
);

class SetupController extends Notifier<SetupState> {
  @override
  SetupState build() => const SetupState();

  Future<MatchSnapshot?> restoreActiveMatch() async {
    if (ref.read(authControllerProvider).isDemo) return state.activeMatch;
    try {
      final match = await ref.read(gameRepositoryProvider).fetchActiveMatch();
      state = state.copyWith(
        activeMatch: match,
        clearActiveMatch: match == null,
      );
      return match;
    } catch (_) {
      return state.activeMatch;
    }
  }

  Future<bool> loadMatch(String matchId) async {
    if (ref.read(authControllerProvider).isDemo) return false;
    state = state.copyWith(isCreating: true, clearError: true);
    try {
      final match = await ref.read(gameRepositoryProvider).fetchMatch(matchId);
      state = state.copyWith(isCreating: false, activeMatch: match);
      return true;
    } catch (_) {
      state = state.copyWith(
        isCreating: false,
        error: 'تعذر تحميل تفاصيل الجولة.',
      );
      return false;
    }
  }

  void clearMatch() {
    state = state.copyWith(clearActiveMatch: true, clearError: true);
  }

  void setCount(int count) {
    final retained = state.selected.take(count).toSet();
    state = state.copyWith(categoryCount: count, selected: retained);
  }

  void toggle(String categoryId) {
    final next = {...state.selected};
    if (!next.remove(categoryId) && next.length < state.categoryCount) {
      next.add(categoryId);
    }
    state = state.copyWith(selected: next, clearError: true);
  }

  void selectRandom(List<CategoryAvailability> categories) {
    final eligible = categories.where((item) => item.eligible).toList()
      ..shuffle(Random.secure());
    if (eligible.length < state.categoryCount) {
      state = state.copyWith(
        selected: eligible.map((item) => item.id).toSet(),
        error: 'لا توجد فئات مؤهلة كافية لهذا العدد.',
      );
      return;
    }
    state = state.copyWith(
      selected: eligible
          .take(state.categoryCount)
          .map((item) => item.id)
          .toSet(),
      clearError: true,
    );
  }

  Future<bool> startMatch({
    required List<CategoryAvailability> allCategories,
    required String teamOne,
    required String teamTwo,
  }) async {
    final selectedCategories = allCategories
        .where((item) => state.selected.contains(item.id))
        .toList();
    state = state.copyWith(isCreating: true, clearError: true);
    try {
      final MatchSnapshot match;
      if (ref.read(authControllerProvider).isDemo) {
        match = MatchSnapshot.demo(
          categories: selectedCategories
              .map(
                (item) =>
                    CategoryAvailabilityReference(id: item.id, name: item.name),
              )
              .toList(),
          teamOne: teamOne,
          teamTwo: teamTwo,
        );
      } else {
        match = await ref
            .read(gameRepositoryProvider)
            .createMatch(
              categories: selectedCategories,
              teamOne: teamOne,
              teamTwo: teamTwo,
            );
      }
      state = state.copyWith(isCreating: false, activeMatch: match);
      return true;
    } catch (_) {
      state = state.copyWith(
        isCreating: false,
        error: 'لم نتمكن من بدء الجولة. تحقق من الاتصال وحاول مرة أخرى.',
      );
      return false;
    }
  }

  Future<bool> openQuestion(
    String questionId, {
    bool doublePoints = false,
  }) async {
    var match = state.activeMatch;
    if (match == null) return false;
    state = state.copyWith(isCreating: true, clearError: true);
    try {
      if (ref.read(authControllerProvider).isDemo) {
        match = _demoOpen(match, questionId, doublePoints: doublePoints);
      } else {
        if (doublePoints) {
          match = await ref
              .read(gameRepositoryProvider)
              .armLifeline(match, 'double_points', questionId);
        }
        match = await ref
            .read(gameRepositoryProvider)
            .openQuestion(match, questionId);
      }
      state = state.copyWith(isCreating: false, activeMatch: match);
      return true;
    } catch (_) {
      state = state.copyWith(
        isCreating: false,
        error: 'تعذر فتح السؤال. حدّث الجولة وحاول مرة أخرى.',
      );
      return false;
    }
  }

  Future<void> useLifeline(String type) async {
    var match = state.activeMatch;
    final question = match?.activeQuestion;
    if (match == null || question == null) return;
    state = state.copyWith(isCreating: true, clearError: true);
    try {
      if (ref.read(authControllerProvider).isDemo) {
        match = match.copyWith(
          version: match.version + 1,
          lifelines: match.lifelines
              .map(
                (item) =>
                    item.teamNumber == match!.currentTeam && item.type == type
                    ? item.copyWith(state: 'used', matchQuestionId: question.id)
                    : item,
              )
              .toList(),
          activeQuestion: type == 'show_options'
              ? question.copyWith(optionsVisible: true)
              : question,
        );
      } else {
        match = await ref
            .read(gameRepositoryProvider)
            .armLifeline(match, type, question.id);
      }
      state = state.copyWith(isCreating: false, activeMatch: match);
    } catch (_) {
      state = state.copyWith(
        isCreating: false,
        error: 'لا يمكن استخدام المساعدة الآن.',
      );
    }
  }

  Future<void> markMediaReady() async {
    var match = state.activeMatch;
    if (match?.activeQuestion == null ||
        match!.activeQuestion!.deadline != null) {
      return;
    }
    if (ref.read(authControllerProvider).isDemo) {
      match = match.copyWith(
        version: match.version + 1,
        activeQuestion: match.activeQuestion!.copyWith(
          deadline: DateTime.now().add(Duration(seconds: match.timerSeconds)),
        ),
      );
    } else {
      match = await ref.read(gameRepositoryProvider).markMediaReady(match);
    }
    state = state.copyWith(activeMatch: match);
  }

  Future<MediaPlaybackSnapshot?> fetchPlayback() async {
    final match = state.activeMatch;
    final mediaId = match?.activeQuestion?.mediaAssetId;
    if (match == null ||
        mediaId == null ||
        ref.read(authControllerProvider).isDemo) {
      return null;
    }
    return ref.read(gameRepositoryProvider).fetchPlayback(match.id, mediaId);
  }

  Future<void> recordMediaPlay() async {
    var match = state.activeMatch;
    final question = match?.activeQuestion;
    if (match == null || question == null) return;
    if (ref.read(authControllerProvider).isDemo) {
      match = match.copyWith(
        version: match.version + 1,
        activeQuestion: question.copyWith(playCount: question.playCount + 1),
      );
    } else {
      match = await ref.read(gameRepositoryProvider).recordMediaPlay(match);
    }
    state = state.copyWith(activeMatch: match);
  }

  Future<void> revealQuestion() async {
    var match = state.activeMatch;
    final question = match?.activeQuestion;
    if (match == null || question == null) return;
    state = state.copyWith(isCreating: true, clearError: true);
    try {
      match = ref.read(authControllerProvider).isDemo
          ? match.copyWith(
              version: match.version + 1,
              activeQuestion: question.copyWith(
                state: 'revealed',
                answer: question.options[1],
              ),
            )
          : await ref.read(gameRepositoryProvider).revealQuestion(match);
      state = state.copyWith(isCreating: false, activeMatch: match);
    } catch (_) {
      state = state.copyWith(isCreating: false, error: 'تعذر إظهار الإجابة.');
    }
  }

  Future<bool> scoreQuestion(int? answeredByTeam) async {
    var match = state.activeMatch;
    final question = match?.activeQuestion;
    if (match == null || question == null) return false;
    state = state.copyWith(isCreating: true, clearError: true);
    try {
      if (ref.read(authControllerProvider).isDemo) {
        final teams = match.teams
            .map(
              (team) => team.number == answeredByTeam
                  ? team.copyWith(score: team.score + question.effectivePoints)
                  : team,
            )
            .toList();
        final categories = match.categories
            .map(
              (category) => category.copyWith(
                questions: category.questions
                    .map(
                      (item) => item.id == question.id
                          ? item.copyWith(state: 'scored')
                          : item,
                    )
                    .toList(),
              ),
            )
            .toList();
        final completed = categories
            .expand((category) => category.questions)
            .every((item) => item.state == 'scored');
        match = match.copyWith(
          status: completed ? 'completed' : match.status,
          version: match.version + 1,
          currentTeam: match.currentTeam == 1 ? 2 : 1,
          teams: teams,
          categories: categories,
          clearActiveQuestion: true,
        );
      } else {
        match = await ref
            .read(gameRepositoryProvider)
            .scoreQuestion(match, answeredByTeam);
      }
      state = state.copyWith(isCreating: false, activeMatch: match);
      return true;
    } catch (_) {
      state = state.copyWith(isCreating: false, error: 'تعذر تسجيل النقاط.');
      return false;
    }
  }

  MatchSnapshot _demoOpen(
    MatchSnapshot match,
    String questionId, {
    required bool doublePoints,
  }) {
    final boardQuestion = match.categories
        .expand((category) => category.questions)
        .firstWhere((question) => question.id == questionId);
    final categories = match.categories
        .map(
          (category) => category.copyWith(
            questions: category.questions
                .map(
                  (question) => question.id == questionId
                      ? question.copyWith(state: 'open')
                      : question,
                )
                .toList(),
          ),
        )
        .toList();
    final prompt = switch (boardQuestion.type) {
      'audio' => 'استمع جيداً… لأي سيارة يعود صوت هذا المحرك؟',
      'video' => 'شاهد المقطع وأكمل الجملة الشهيرة.',
      'image' => 'أي مدينة عربية تظهر في هذه الصورة؟',
      _ => 'ما هي عاصمة الدولة العربية الأكبر مساحة؟',
    };
    return match.copyWith(
      version: match.version + (doublePoints ? 2 : 1),
      categories: categories,
      lifelines: doublePoints
          ? match.lifelines
                .map(
                  (item) =>
                      item.teamNumber == match.currentTeam &&
                          item.type == 'double_points'
                      ? item.copyWith(
                          state: 'used',
                          matchQuestionId: questionId,
                        )
                      : item,
                )
                .toList()
          : match.lifelines,
      activeQuestion: ActiveQuestionSnapshot(
        id: questionId,
        type: boardQuestion.type,
        prompt: prompt,
        options: const ['السعودية', 'الجزائر', 'السودان', 'مصر'],
        optionsVisible: false,
        points: boardQuestion.points,
        effectivePoints: boardQuestion.points * (doublePoints ? 2 : 1),
        state: 'open',
        playCount: 0,
        maxPlays: ['audio', 'video'].contains(boardQuestion.type) ? 2 : null,
        choosingTeam: match.currentTeam,
        deadline: boardQuestion.type == 'text'
            ? DateTime.now().add(Duration(seconds: match.timerSeconds))
            : null,
      ),
    );
  }
}
