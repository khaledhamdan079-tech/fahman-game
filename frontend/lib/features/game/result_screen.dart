import 'package:fahman/core/theme/app_theme.dart';
import 'package:fahman/features/match_setup/presentation/setup_controller.dart';
import 'package:fahman/shared/widgets/game_background.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class ResultScreen extends ConsumerWidget {
  const ResultScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final match = ref.watch(setupControllerProvider).activeMatch;
    if (match == null || match.teams.length < 2) {
      return Scaffold(
        body: Center(
          child: FilledButton(
            onPressed: () => context.go('/history'),
            child: const Text('عرض الجولات السابقة'),
          ),
        ),
      );
    }
    final first = match.teams[0];
    final second = match.teams[1];
    final tied = first.score == second.score;
    final winner = first.score > second.score ? first : second;
    final usedLifelines = match.lifelines
        .where((item) => item.state != 'available')
        .length;

    return Scaffold(
      body: GameBackground(
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(22),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 720),
                child: Container(
                  padding: const EdgeInsets.all(28),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(32),
                    border: Border.all(color: FahmanColors.line),
                  ),
                  child: Column(
                    children: [
                      Container(
                        width: 100,
                        height: 100,
                        decoration: const BoxDecoration(
                          color: FahmanColors.saffron,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          tied ? Icons.handshake_rounded : Icons.emoji_events,
                          size: 58,
                          color: FahmanColors.midnight,
                        ),
                      ),
                      const SizedBox(height: 18),
                      Text(
                        tied ? 'تعادل الفهمانين!' : 'الفوز لـ ${winner.name}!',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.headlineLarge,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '${match.categories.length} فئات • $usedLifelines مساعدات مستخدمة',
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                      const SizedBox(height: 26),
                      Row(
                        children: [
                          Expanded(
                            child: _FinalScore(
                              name: first.name,
                              score: first.score,
                              color: FahmanColors.coral,
                            ),
                          ),
                          const Padding(
                            padding: EdgeInsets.symmetric(horizontal: 10),
                            child: Text('—'),
                          ),
                          Expanded(
                            child: _FinalScore(
                              name: second.name,
                              score: second.score,
                              color: FahmanColors.purple,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 28),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton.icon(
                          onPressed: () {
                            ref
                                .read(setupControllerProvider.notifier)
                                .clearMatch();
                            context.go('/setup/categories');
                          },
                          icon: const Icon(Icons.replay_rounded),
                          label: const Text('جولة جديدة'),
                        ),
                      ),
                      const SizedBox(height: 10),
                      TextButton(
                        onPressed: () => context.go('/home'),
                        child: const Text('العودة للرئيسية'),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _FinalScore extends StatelessWidget {
  const _FinalScore({
    required this.name,
    required this.score,
    required this.color,
  });
  final String name;
  final int score;
  final Color color;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 20),
    decoration: BoxDecoration(
      color: color.withValues(alpha: 0.12),
      borderRadius: BorderRadius.circular(22),
    ),
    child: Column(
      children: [
        Text(
          name,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        Text(
          '$score',
          style: TextStyle(
            color: color,
            fontSize: 38,
            fontWeight: FontWeight.w900,
          ),
        ),
      ],
    ),
  );
}
