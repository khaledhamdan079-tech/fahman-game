import 'package:fahman/core/theme/app_theme.dart';
import 'package:fahman/features/authentication/presentation/auth_controller.dart';
import 'package:fahman/features/match_setup/presentation/setup_controller.dart';
import 'package:fahman/shared/widgets/fahman_logo.dart';
import 'package:fahman/shared/widgets/game_background.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(
      () => ref.read(setupControllerProvider.notifier).restoreActiveMatch(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final activeMatch = ref.watch(setupControllerProvider).activeMatch;
    final firstName = auth.user?.displayName.split(' ').first ?? 'يا فهمان';
    return Scaffold(
      body: GameBackground(
        child: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 980),
              child: ListView(
                padding: const EdgeInsets.fromLTRB(22, 18, 22, 28),
                children: [
                  Row(
                    children: [
                      const FahmanLogo(compact: true),
                      const Spacer(),
                      IconButton.filledTonal(
                        tooltip: 'تسجيل الخروج',
                        onPressed: () async {
                          ref
                              .read(setupControllerProvider.notifier)
                              .clearMatch();
                          await ref
                              .read(authControllerProvider.notifier)
                              .signOut();
                          if (context.mounted) context.go('/');
                        },
                        icon: const Icon(Icons.logout_rounded),
                      ),
                    ],
                  ),
                  const SizedBox(height: 42),
                  Text(
                    'هلا $firstName 👋',
                    style: Theme.of(context).textTheme.headlineLarge,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'من سيحمل لقب فهمان اليوم؟',
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                  const SizedBox(height: 26),
                  _NewMatchCard(onTap: () => context.go('/setup/categories')),
                  if (activeMatch?.status == 'active') ...[
                    const SizedBox(height: 16),
                    _ResumeMatchCard(
                      teamNames: activeMatch!.teams
                          .map((team) => team.name)
                          .join(' × '),
                      onTap: () => context.go(
                        activeMatch.activeQuestion == null
                            ? '/game'
                            : '/question',
                      ),
                    ),
                  ],
                  const SizedBox(height: 20),
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final wide = constraints.maxWidth > 620;
                      if (wide) {
                        return Row(
                          children: [
                            Expanded(
                              child: _SmallCard(
                                icon: Icons.history_rounded,
                                title: 'الجولات السابقة',
                                subtitle: 'راجع النتائج والمواجهات',
                                onTap: () => context.go('/history'),
                              ),
                            ),
                            SizedBox(width: 16),
                            Expanded(
                              child: _SmallCard(
                                icon: Icons.auto_awesome_rounded,
                                title: 'رصيد الأسئلة',
                                subtitle: 'شاهد الفئات الجاهزة للعب',
                              ),
                            ),
                          ],
                        );
                      }
                      return Column(
                        children: [
                          _SmallCard(
                            icon: Icons.history_rounded,
                            title: 'الجولات السابقة',
                            subtitle: 'راجع النتائج والمواجهات',
                            onTap: () => context.go('/history'),
                          ),
                          SizedBox(height: 16),
                          _SmallCard(
                            icon: Icons.auto_awesome_rounded,
                            title: 'رصيد الأسئلة',
                            subtitle: 'شاهد الفئات الجاهزة للعب',
                          ),
                        ],
                      );
                    },
                  ),
                  if (auth.isDemo) ...[
                    const SizedBox(height: 18),
                    const _DemoNotice(),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _NewMatchCard extends StatelessWidget {
  const _NewMatchCard({required this.onTap});
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Material(
    color: FahmanColors.midnight,
    borderRadius: BorderRadius.circular(30),
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(30),
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Row(
          children: [
            Container(
              width: 70,
              height: 70,
              decoration: BoxDecoration(
                color: FahmanColors.saffron,
                borderRadius: BorderRadius.circular(22),
              ),
              child: const Icon(
                Icons.bolt_rounded,
                size: 42,
                color: FahmanColors.midnight,
              ),
            ),
            const SizedBox(width: 20),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'جولة جديدة',
                    style: Theme.of(
                      context,
                    ).textTheme.headlineMedium?.copyWith(color: Colors.white),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    'اختر الفئات وجهّز الفريقين',
                    style: Theme.of(
                      context,
                    ).textTheme.bodyMedium?.copyWith(color: Colors.white70),
                  ),
                ],
              ),
            ),
            const Icon(Icons.arrow_back_rounded, color: Colors.white, size: 30),
          ],
        ),
      ),
    ),
  );
}

class _ResumeMatchCard extends StatelessWidget {
  const _ResumeMatchCard({required this.teamNames, required this.onTap});
  final String teamNames;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Material(
    color: FahmanColors.turquoise.withValues(alpha: 0.16),
    borderRadius: BorderRadius.circular(24),
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(24),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            const CircleAvatar(
              backgroundColor: FahmanColors.turquoise,
              foregroundColor: FahmanColors.midnight,
              child: Icon(Icons.play_arrow_rounded),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'كمّل الجولة',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  Text(teamNames),
                ],
              ),
            ),
            const Icon(Icons.arrow_back_rounded),
          ],
        ),
      ),
    ),
  );
}

class _SmallCard extends StatelessWidget {
  const _SmallCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    this.onTap,
  });
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => Material(
    color: Colors.white,
    borderRadius: BorderRadius.circular(24),
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(24),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: FahmanColors.line),
        ),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: FahmanColors.purple.withValues(alpha: 0.12),
              foregroundColor: FahmanColors.purple,
              child: Icon(icon),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleLarge),
                  Text(subtitle, style: Theme.of(context).textTheme.bodyMedium),
                ],
              ),
            ),
          ],
        ),
      ),
    ),
  );
}

class _DemoNotice extends StatelessWidget {
  const _DemoNotice();

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(15),
    decoration: BoxDecoration(
      color: FahmanColors.saffron.withValues(alpha: 0.22),
      borderRadius: BorderRadius.circular(18),
    ),
    child: const Row(
      children: [
        Icon(Icons.science_rounded, color: FahmanColors.saffronDark),
        SizedBox(width: 10),
        Expanded(
          child: Text('أنت في وضع الاستعراض؛ سنستخدم فئات وجولة تجريبية.'),
        ),
      ],
    ),
  );
}
