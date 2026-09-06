class MatchTeamSnapshot {
  const MatchTeamSnapshot({
    required this.number,
    required this.name,
    required this.score,
  });

  factory MatchTeamSnapshot.fromJson(Map<String, dynamic> json) =>
      MatchTeamSnapshot(
        number: json['team_no'] as int,
        name: json['name'] as String,
        score: json['score'] as int,
      );

  final int number;
  final String name;
  final int score;

  MatchTeamSnapshot copyWith({int? score}) =>
      MatchTeamSnapshot(number: number, name: name, score: score ?? this.score);
}

class MatchHistoryItem {
  const MatchHistoryItem({
    required this.id,
    required this.status,
    required this.createdAt,
    required this.teams,
    this.finishedAt,
  });

  factory MatchHistoryItem.fromJson(Map<String, dynamic> json) =>
      MatchHistoryItem(
        id: json['id'] as String,
        status: json['status'] as String,
        createdAt: DateTime.parse(json['created_at'] as String),
        finishedAt: json['finished_at'] == null
            ? null
            : DateTime.parse(json['finished_at'] as String),
        teams: (json['teams'] as List<dynamic>)
            .map(
              (item) =>
                  MatchTeamSnapshot.fromJson(item as Map<String, dynamic>),
            )
            .toList(),
      );

  final String id;
  final String status;
  final DateTime createdAt;
  final DateTime? finishedAt;
  final List<MatchTeamSnapshot> teams;
}

class BoardQuestionSnapshot {
  const BoardQuestionSnapshot({
    required this.id,
    required this.points,
    required this.type,
    required this.state,
  });

  factory BoardQuestionSnapshot.fromJson(Map<String, dynamic> json) =>
      BoardQuestionSnapshot(
        id: json['id'] as String,
        points: json['points'] as int,
        type: json['question_type'] as String,
        state: json['state'] as String,
      );

  final String id;
  final int points;
  final String type;
  final String state;

  BoardQuestionSnapshot copyWith({String? state}) => BoardQuestionSnapshot(
    id: id,
    points: points,
    type: type,
    state: state ?? this.state,
  );
}

class MatchCategorySnapshot {
  const MatchCategorySnapshot({
    required this.id,
    required this.name,
    required this.questions,
  });

  factory MatchCategorySnapshot.fromJson(Map<String, dynamic> json) =>
      MatchCategorySnapshot(
        id: json['id'] as String,
        name: json['name_ar'] as String,
        questions: (json['questions'] as List<dynamic>)
            .map(
              (item) =>
                  BoardQuestionSnapshot.fromJson(item as Map<String, dynamic>),
            )
            .toList(),
      );

  final String id;
  final String name;
  final List<BoardQuestionSnapshot> questions;

  MatchCategorySnapshot copyWith({List<BoardQuestionSnapshot>? questions}) =>
      MatchCategorySnapshot(
        id: id,
        name: name,
        questions: questions ?? this.questions,
      );
}

class LifelineSnapshot {
  const LifelineSnapshot({
    required this.teamNumber,
    required this.type,
    required this.state,
    this.matchQuestionId,
  });

  factory LifelineSnapshot.fromJson(Map<String, dynamic> json) =>
      LifelineSnapshot(
        teamNumber: json['team_no'] as int,
        type: json['lifeline_type'] as String,
        state: json['state'] as String,
        matchQuestionId: json['match_question_id'] as String?,
      );

  final int teamNumber;
  final String type;
  final String state;
  final String? matchQuestionId;

  LifelineSnapshot copyWith({String? state, String? matchQuestionId}) =>
      LifelineSnapshot(
        teamNumber: teamNumber,
        type: type,
        state: state ?? this.state,
        matchQuestionId: matchQuestionId ?? this.matchQuestionId,
      );
}

class ActiveQuestionSnapshot {
  const ActiveQuestionSnapshot({
    required this.id,
    required this.type,
    required this.prompt,
    required this.options,
    required this.points,
    required this.effectivePoints,
    required this.state,
    required this.playCount,
    required this.choosingTeam,
    this.answer,
    this.mediaAssetId,
    this.deadline,
    this.maxPlays,
  });

  factory ActiveQuestionSnapshot.fromJson(Map<String, dynamic> json) =>
      ActiveQuestionSnapshot(
        id: json['id'] as String,
        type: json['question_type'] as String,
        prompt: json['prompt_ar'] as String,
        options: (json['options'] as List<dynamic>)
            .map((item) => (item as Map<String, dynamic>)['text_ar'] as String)
            .toList(),
        answer: json['answer_ar'] as String?,
        points: json['points'] as int,
        effectivePoints: json['effective_points'] as int,
        state: json['state'] as String,
        mediaAssetId: json['media_asset_id'] as String?,
        deadline: json['deadline_at'] == null
            ? null
            : DateTime.parse(json['deadline_at'] as String),
        playCount: json['play_count'] as int,
        maxPlays: json['max_plays'] as int?,
        choosingTeam: json['choosing_team_no'] as int,
      );

  final String id;
  final String type;
  final String prompt;
  final List<String> options;
  final String? answer;
  final int points;
  final int effectivePoints;
  final String state;
  final String? mediaAssetId;
  final DateTime? deadline;
  final int playCount;
  final int? maxPlays;
  final int choosingTeam;

  ActiveQuestionSnapshot copyWith({
    String? answer,
    String? state,
    DateTime? deadline,
    int? playCount,
  }) => ActiveQuestionSnapshot(
    id: id,
    type: type,
    prompt: prompt,
    options: options,
    answer: answer ?? this.answer,
    points: points,
    effectivePoints: effectivePoints,
    state: state ?? this.state,
    mediaAssetId: mediaAssetId,
    deadline: deadline ?? this.deadline,
    playCount: playCount ?? this.playCount,
    maxPlays: maxPlays,
    choosingTeam: choosingTeam,
  );
}

class MatchSnapshot {
  const MatchSnapshot({
    required this.id,
    required this.status,
    required this.currentTeam,
    required this.timerSeconds,
    required this.version,
    required this.teams,
    required this.categories,
    required this.lifelines,
    this.activeQuestion,
  });

  factory MatchSnapshot.fromJson(Map<String, dynamic> json) => MatchSnapshot(
    id: json['id'] as String,
    status: json['status'] as String,
    currentTeam: json['current_team_no'] as int,
    timerSeconds: json['timer_seconds'] as int,
    version: json['version'] as int,
    teams: (json['teams'] as List<dynamic>)
        .map((item) => MatchTeamSnapshot.fromJson(item as Map<String, dynamic>))
        .toList(),
    categories: (json['categories'] as List<dynamic>)
        .map(
          (item) =>
              MatchCategorySnapshot.fromJson(item as Map<String, dynamic>),
        )
        .toList(),
    lifelines: (json['lifelines'] as List<dynamic>)
        .map((item) => LifelineSnapshot.fromJson(item as Map<String, dynamic>))
        .toList(),
    activeQuestion: json['active_question'] == null
        ? null
        : ActiveQuestionSnapshot.fromJson(
            json['active_question'] as Map<String, dynamic>,
          ),
  );

  factory MatchSnapshot.demo({
    required List<CategoryAvailabilityReference> categories,
    required String teamOne,
    required String teamTwo,
  }) => MatchSnapshot(
    id: 'demo-match',
    status: 'active',
    currentTeam: 1,
    timerSeconds: 60,
    version: 1,
    teams: [
      MatchTeamSnapshot(number: 1, name: teamOne, score: 0),
      MatchTeamSnapshot(number: 2, name: teamTwo, score: 0),
    ],
    categories: categories
        .map(
          (category) => MatchCategorySnapshot(
            id: category.id,
            name: category.name,
            questions: [
              for (var index = 0; index < 6; index++)
                BoardQuestionSnapshot(
                  id: '${category.id}-$index',
                  points: index < 2 ? 200 : (index < 4 ? 400 : 600),
                  type: index == 2 ? 'audio' : (index == 4 ? 'video' : 'text'),
                  state: 'available',
                ),
            ],
          ),
        )
        .toList(),
    lifelines: [
      for (final team in [1, 2])
        for (final type in ['two_answers', 'double_points', 'block_opponent'])
          LifelineSnapshot(teamNumber: team, type: type, state: 'available'),
    ],
  );

  final String id;
  final String status;
  final int currentTeam;
  final int timerSeconds;
  final int version;
  final List<MatchTeamSnapshot> teams;
  final List<MatchCategorySnapshot> categories;
  final List<LifelineSnapshot> lifelines;
  final ActiveQuestionSnapshot? activeQuestion;

  MatchSnapshot copyWith({
    String? status,
    int? currentTeam,
    int? version,
    List<MatchTeamSnapshot>? teams,
    List<MatchCategorySnapshot>? categories,
    List<LifelineSnapshot>? lifelines,
    ActiveQuestionSnapshot? activeQuestion,
    bool clearActiveQuestion = false,
  }) => MatchSnapshot(
    id: id,
    status: status ?? this.status,
    currentTeam: currentTeam ?? this.currentTeam,
    timerSeconds: timerSeconds,
    version: version ?? this.version,
    teams: teams ?? this.teams,
    categories: categories ?? this.categories,
    lifelines: lifelines ?? this.lifelines,
    activeQuestion: clearActiveQuestion
        ? null
        : activeQuestion ?? this.activeQuestion,
  );
}

class CategoryAvailabilityReference {
  const CategoryAvailabilityReference({required this.id, required this.name});
  final String id;
  final String name;
}

class MediaPlaybackSnapshot {
  const MediaPlaybackSnapshot({
    required this.url,
    this.posterUrl,
    this.durationMs,
  });

  factory MediaPlaybackSnapshot.fromJson(Map<String, dynamic> json) =>
      MediaPlaybackSnapshot(
        url: json['url'] as String,
        posterUrl: json['poster_url'] as String?,
        durationMs: json['duration_ms'] as int?,
      );

  final String url;
  final String? posterUrl;
  final int? durationMs;
}
