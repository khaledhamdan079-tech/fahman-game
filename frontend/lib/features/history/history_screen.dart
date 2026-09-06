import 'package:fahman/core/theme/app_theme.dart';
import 'package:fahman/features/authentication/presentation/auth_controller.dart';
import 'package:fahman/features/match_setup/domain/match_snapshot.dart';
import 'package:fahman/features/match_setup/presentation/setup_controller.dart';
import 'package:fahman/shared/widgets/game_background.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

final matchHistoryProvider = FutureProvider<List<MatchHistoryItem>>((ref) {
  if (ref.watch(authControllerProvider).isDemo) {
    final now = DateTime.now();
    return Future.value([
      MatchHistoryItem(
        id: 'demo-history-1',
        status: 'completed',
        createdAt: now.subtract(const Duration(days: 1)),
        finishedAt: now.subtract(const Duration(days: 1, hours: -1)),
        teams: const [
          MatchTeamSnapshot(number: 1, name: 'الصقور', score: 2400),
          MatchTeamSnapshot(number: 2, name: 'النوابغ', score: 2200),
        ],
      ),
      MatchHistoryItem(
        id: 'demo-history-2',
        status: 'completed',
        createdAt: now.subtract(const Duration(days: 4)),
        teams: const [
          MatchTeamSnapshot(number: 1, name: 'الأبطال', score: 1800),
          MatchTeamSnapshot(number: 2, name: 'الفهمانين', score: 2600),
        ],
      ),
    ]);
  }
  return ref.watch(gameRepositoryProvider).fetchHistory();
});

class HistoryScreen extends ConsumerWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final history = ref.watch(matchHistoryProvider);
    return Scaffold(
      body: GameBackground(
        child: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 820),
              child: Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 10),
                    child: Row(
                      children: [
                        IconButton.filledTonal(
                          onPressed: () => context.go('/home'),
                          icon: const Icon(Icons.arrow_forward_rounded),
                        ),
                        const SizedBox(width: 12),
                        Text(
                          'الجولات السابقة',
                          style: Theme.of(context).textTheme.headlineMedium,
                        ),
                      ],
                    ),
                  ),
                  Expanded(
                    child: history.when(
                      loading: () =>
                          const Center(child: CircularProgressIndicator()),
                      error: (_, _) => _HistoryMessage(
                        icon: Icons.cloud_off_rounded,
                        title: 'تعذر تحميل الجولات',
                        action: () => ref.invalidate(matchHistoryProvider),
                      ),
                      data: (items) => items.isEmpty
                          ? const _HistoryMessage(
                              icon: Icons.sports_score_rounded,
                              title: 'لا توجد جولات سابقة بعد',
                            )
                          : RefreshIndicator(
                              onRefresh: () async =>
                                  ref.refresh(matchHistoryProvider.future),
                              child: ListView.separated(
                                padding: const EdgeInsets.fromLTRB(
                                  18,
                                  10,
                                  18,
                                  30,
                                ),
                                itemCount: items.length,
                                separatorBuilder: (_, _) =>
                                    const SizedBox(height: 12),
                                itemBuilder: (context, index) => _HistoryCard(
                                  item: items[index],
                                  onTap: () =>
                                      _openMatch(context, ref, items[index]),
                                ),
                              ),
                            ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _openMatch(
    BuildContext context,
    WidgetRef ref,
    MatchHistoryItem item,
  ) async {
    if (ref.read(authControllerProvider).isDemo) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('تفاصيل الجولة متاحة بعد تسجيل الدخول.')),
      );
      return;
    }
    final loaded = await ref
        .read(setupControllerProvider.notifier)
        .loadMatch(item.id);
    if (!loaded || !context.mounted) return;
    context.go(item.status == 'completed' ? '/result' : '/game');
  }
}

class _HistoryCard extends StatelessWidget {
  const _HistoryCard({required this.item, required this.onTap});
  final MatchHistoryItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final first = item.teams[0];
    final second = item.teams[1];
    final completed = item.status == 'completed';
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(24),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(24),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              Row(
                children: [
                  Chip(
                    avatar: Icon(
                      completed ? Icons.check_circle_rounded : Icons.timelapse,
                      size: 18,
                    ),
                    label: Text(completed ? 'مكتملة' : 'غير مكتملة'),
                  ),
                  const Spacer(),
                  Text(_dateLabel(item.createdAt)),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(child: _TeamResult(team: first)),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 12),
                    child: Text('ضد'),
                  ),
                  Expanded(child: _TeamResult(team: second)),
                  const SizedBox(width: 8),
                  const Icon(Icons.arrow_back_rounded),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  static String _dateLabel(DateTime date) =>
      '${date.year}/${date.month.toString().padLeft(2, '0')}/${date.day.toString().padLeft(2, '0')}';
}

class _TeamResult extends StatelessWidget {
  const _TeamResult({required this.team});
  final MatchTeamSnapshot team;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Text(
        team.name,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(fontWeight: FontWeight.w800),
      ),
      Text(
        '${team.score}',
        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
          color: FahmanColors.purple,
          fontWeight: FontWeight.w900,
        ),
      ),
    ],
  );
}

class _HistoryMessage extends StatelessWidget {
  const _HistoryMessage({required this.icon, required this.title, this.action});
  final IconData icon;
  final String title;
  final VoidCallback? action;

  @override
  Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 64, color: FahmanColors.purple),
        const SizedBox(height: 12),
        Text(title, style: Theme.of(context).textTheme.titleLarge),
        if (action != null)
          TextButton(onPressed: action, child: const Text('حاول مرة أخرى')),
      ],
    ),
  );
}
