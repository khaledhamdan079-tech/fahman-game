import 'package:fahman/core/theme/app_theme.dart';
import 'package:fahman/features/match_setup/domain/match_snapshot.dart';
import 'package:fahman/features/match_setup/presentation/setup_controller.dart';
import 'package:fahman/shared/widgets/fahman_logo.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class GameBoardScreen extends ConsumerWidget {
  const GameBoardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final setup = ref.watch(setupControllerProvider);
    final match = setup.activeMatch;
    if (match == null) {
      return Scaffold(
        body: Center(
          child: FilledButton(
            onPressed: () => context.go('/home'),
            child: const Text('العودة للرئيسية'),
          ),
        ),
      );
    }
    return Scaffold(
      backgroundColor: FahmanColors.midnight,
      body: SafeArea(
        child: Stack(
          children: [
            Column(
              children: [
                _BoardHeader(match: match),
                Expanded(
                  child: _BoardCategories(
                    match: match,
                    onQuestionTap: (question) =>
                        _openQuestion(context, ref, match, question),
                  ),
                ),
                _LifelineBar(match: match),
              ],
            ),
            if (setup.isCreating)
              const Positioned.fill(
                child: ColoredBox(
                  color: Color(0x880B1329),
                  child: Center(
                    child: CircularProgressIndicator(
                      color: FahmanColors.saffron,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _openQuestion(
    BuildContext context,
    WidgetRef ref,
    MatchSnapshot match,
    BoardQuestionSnapshot question,
  ) async {
    if (!['available', 'prepared'].contains(question.state)) return;
    if (question.state == 'prepared') {
      final opened = await ref
          .read(setupControllerProvider.notifier)
          .openQuestion(question.id);
      if (opened && context.mounted) context.go('/question');
      return;
    }
    final doubleAvailable = match.lifelines.any(
      (item) =>
          item.teamNumber == match.currentTeam &&
          item.type == 'double_points' &&
          item.state == 'available',
    );
    final useDouble = await showModalBottomSheet<bool>(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        padding: const EdgeInsets.fromLTRB(22, 18, 22, 28),
        decoration: const BoxDecoration(
          color: FahmanColors.cream,
          borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'سؤال بـ ${question.points} نقطة',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 7),
            const Text('هل تريد فتحه مباشرة أم مضاعفة نقاطه أولاً؟'),
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: () => Navigator.pop(context, false),
              icon: const Icon(Icons.visibility_rounded),
              label: const Text('افتح السؤال'),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: doubleAvailable
                  ? () => Navigator.pop(context, true)
                  : null,
              icon: const Icon(Icons.exposure_plus_2_rounded),
              label: Text(
                doubleAvailable
                    ? 'دبل النقاط ثم افتح'
                    : 'تم استخدام دبل النقاط',
              ),
            ),
          ],
        ),
      ),
    );
    if (useDouble == null) return;
    final opened = await ref
        .read(setupControllerProvider.notifier)
        .openQuestion(question.id, doublePoints: useDouble);
    if (opened && context.mounted) context.go('/question');
  }
}

class _BoardHeader extends StatelessWidget {
  const _BoardHeader({required this.match});
  final MatchSnapshot match;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
    child: Row(
      children: [
        const FahmanLogo(compact: true, light: true),
        const SizedBox(width: 18),
        Expanded(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _ScoreCard(
                team: match.teams[0],
                active: match.currentTeam == 1,
                color: FahmanColors.coral,
              ),
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 10),
                child: Text('ضد', style: TextStyle(color: Colors.white54)),
              ),
              _ScoreCard(
                team: match.teams[1],
                active: match.currentTeam == 2,
                color: FahmanColors.purple,
              ),
            ],
          ),
        ),
        IconButton(
          tooltip: 'العودة للرئيسية',
          onPressed: () => context.go('/home'),
          color: Colors.white,
          icon: const Icon(Icons.close_rounded),
        ),
      ],
    ),
  );
}

class _ScoreCard extends StatelessWidget {
  const _ScoreCard({
    required this.team,
    required this.active,
    required this.color,
  });
  final MatchTeamSnapshot team;
  final bool active;
  final Color color;

  @override
  Widget build(BuildContext context) => AnimatedContainer(
    duration: const Duration(milliseconds: 220),
    constraints: const BoxConstraints(minWidth: 122),
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
    decoration: BoxDecoration(
      color: active ? color : FahmanColors.midnightSoft,
      borderRadius: BorderRadius.circular(18),
      border: Border.all(
        color: active ? FahmanColors.saffron : Colors.white12,
        width: 2,
      ),
    ),
    child: Column(
      children: [
        Text(
          team.name,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w800,
          ),
        ),
        Text(
          '${team.score}',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 24,
            fontWeight: FontWeight.w900,
            height: 1.1,
          ),
        ),
      ],
    ),
  );
}

class _BoardCategories extends StatelessWidget {
  const _BoardCategories({required this.match, required this.onQuestionTap});
  final MatchSnapshot match;
  final ValueChanged<BoardQuestionSnapshot> onQuestionTap;

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final columnWidth = (constraints.maxWidth / match.categories.length)
          .clamp(150.0, 220.0)
          .toDouble();
      return SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            for (final category in match.categories)
              SizedBox(
                width: columnWidth,
                child: _CategoryColumn(
                  category: category,
                  onQuestionTap: onQuestionTap,
                ),
              ),
          ],
        ),
      );
    },
  );
}

class _CategoryColumn extends StatelessWidget {
  const _CategoryColumn({required this.category, required this.onQuestionTap});
  final MatchCategorySnapshot category;
  final ValueChanged<BoardQuestionSnapshot> onQuestionTap;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 5),
    child: Column(
      children: [
        Container(
          width: double.infinity,
          height: 62,
          padding: const EdgeInsets.symmetric(horizontal: 8),
          alignment: Alignment.center,
          decoration: const BoxDecoration(
            color: FahmanColors.saffron,
            borderRadius: BorderRadius.vertical(top: Radius.circular(18)),
          ),
          child: Text(
            category.name,
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: FahmanColors.midnight,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
        const SizedBox(height: 6),
        for (final question in category.questions)
          Expanded(
            child: _QuestionTile(
              question: question,
              onTap: () => onQuestionTap(question),
            ),
          ),
      ],
    ),
  );
}

class _QuestionTile extends StatelessWidget {
  const _QuestionTile({required this.question, required this.onTap});
  final BoardQuestionSnapshot question;
  final VoidCallback onTap;

  IconData get mediaIcon => switch (question.type) {
    'audio' => Icons.graphic_eq_rounded,
    'video' => Icons.play_circle_fill_rounded,
    'image' => Icons.image_rounded,
    _ => Icons.help_rounded,
  };

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 6),
    child: Material(
      color: ['available', 'prepared'].contains(question.state)
          ? FahmanColors.midnightSoft
          : Colors.white10,
      borderRadius: BorderRadius.circular(13),
      child: InkWell(
        borderRadius: BorderRadius.circular(13),
        onTap: ['available', 'prepared'].contains(question.state)
            ? onTap
            : null,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                question.state == 'available'
                    ? '${question.points}'
                    : question.state == 'prepared'
                    ? 'دبل ${question.points}'
                    : '✓',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 21,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(width: 7),
              Icon(mediaIcon, color: FahmanColors.turquoise, size: 17),
            ],
          ),
        ),
      ),
    ),
  );
}

class _LifelineBar extends StatelessWidget {
  const _LifelineBar({required this.match});
  final MatchSnapshot match;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.fromLTRB(16, 10, 16, 14),
    decoration: const BoxDecoration(
      color: Color(0xFF0B1329),
      border: Border(top: BorderSide(color: Colors.white12)),
    ),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          'دور ${match.teams[match.currentTeam - 1].name}',
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(width: 16),
        _LifelineBadge(
          icon: Icons.looks_two_rounded,
          label: 'إجابتان',
          used: _isUsed('two_answers'),
        ),
        _LifelineBadge(
          icon: Icons.exposure_plus_2_rounded,
          label: 'دبل',
          used: _isUsed('double_points'),
        ),
        _LifelineBadge(
          icon: Icons.block_rounded,
          label: 'حجب',
          used: _isUsed('block_opponent'),
        ),
      ],
    ),
  );

  bool _isUsed(String type) => match.lifelines.any(
    (item) =>
        item.teamNumber == match.currentTeam &&
        item.type == type &&
        item.state != 'available',
  );
}

class _LifelineBadge extends StatelessWidget {
  const _LifelineBadge({
    required this.icon,
    required this.label,
    required this.used,
  });
  final IconData icon;
  final String label;
  final bool used;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsetsDirectional.only(start: 8),
    child: Chip(
      avatar: Icon(
        icon,
        size: 17,
        color: used ? Colors.white38 : FahmanColors.saffron,
      ),
      label: Text(used ? '$label ✓' : label),
      backgroundColor: FahmanColors.midnightSoft,
      side: BorderSide(color: used ? Colors.white10 : Colors.white24),
      labelStyle: TextStyle(color: used ? Colors.white38 : Colors.white),
    ),
  );
}
