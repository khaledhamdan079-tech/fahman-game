import 'package:fahman/core/theme/app_theme.dart';
import 'package:fahman/features/match_setup/domain/category_availability.dart';
import 'package:fahman/features/match_setup/presentation/setup_controller.dart';
import 'package:fahman/shared/widgets/game_background.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class CategorySelectionScreen extends ConsumerWidget {
  const CategorySelectionScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final setup = ref.watch(setupControllerProvider);
    final categories = ref.watch(categoriesProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('اختيار الفئات'),
        leading: IconButton(
          onPressed: () => context.go('/home'),
          icon: const Icon(Icons.arrow_forward_rounded),
        ),
      ),
      body: GameBackground(
        child: SafeArea(
          top: false,
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 6, 20, 18),
                child: _CountChooser(selected: setup.categoryCount),
              ),
              Expanded(
                child: categories.when(
                  loading: () =>
                      const Center(child: CircularProgressIndicator()),
                  error: (error, stackTrace) => _LoadError(
                    onRetry: () => ref.invalidate(categoriesProvider),
                  ),
                  data: (items) => Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.fromLTRB(20, 0, 20, 14),
                        child: Row(
                          children: [
                            Text(
                              'أو خلّ فهمان يختار',
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            const Spacer(),
                            OutlinedButton.icon(
                              onPressed: () => ref
                                  .read(setupControllerProvider.notifier)
                                  .selectRandom(items),
                              icon: const Icon(Icons.casino_rounded),
                              label: const Text('اختيار عشوائي'),
                            ),
                          ],
                        ),
                      ),
                      Expanded(
                        child: _CategoryGrid(
                          categories: items,
                          selected: setup.selected,
                          maximum: setup.categoryCount,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.fromLTRB(20, 14, 20, 18),
                decoration: const BoxDecoration(
                  color: Colors.white,
                  border: Border(top: BorderSide(color: FahmanColors.line)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (setup.error != null) ...[
                      Text(
                        setup.error!,
                        style: const TextStyle(
                          color: FahmanColors.coral,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 8),
                    ],
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            'اخترت ${setup.selected.length} من ${setup.categoryCount}',
                            style: const TextStyle(fontWeight: FontWeight.w800),
                          ),
                        ),
                        FilledButton.icon(
                          onPressed:
                              setup.selected.length == setup.categoryCount
                              ? () => context.go('/setup/teams')
                              : null,
                          icon: const Icon(Icons.arrow_back_rounded),
                          label: const Text('التالي'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CountChooser extends ConsumerWidget {
  const _CountChooser({required this.selected});
  final int selected;

  @override
  Widget build(BuildContext context, WidgetRef ref) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(18),
    decoration: BoxDecoration(
      color: FahmanColors.midnight,
      borderRadius: BorderRadius.circular(24),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'كم فئة في هذه الجولة؟',
          style: TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: 13),
        Wrap(
          spacing: 8,
          children: [
            for (var count = 3; count <= 7; count++)
              ChoiceChip(
                selected: count == selected,
                showCheckmark: false,
                label: Text('$count'),
                onSelected: (_) =>
                    ref.read(setupControllerProvider.notifier).setCount(count),
                selectedColor: FahmanColors.saffron,
                backgroundColor: FahmanColors.midnightSoft,
                side: BorderSide.none,
                labelStyle: TextStyle(
                  color: count == selected
                      ? FahmanColors.midnight
                      : Colors.white,
                  fontWeight: FontWeight.w900,
                ),
              ),
          ],
        ),
      ],
    ),
  );
}

class _CategoryGrid extends ConsumerWidget {
  const _CategoryGrid({
    required this.categories,
    required this.selected,
    required this.maximum,
  });
  final List<CategoryAvailability> categories;
  final Set<String> selected;
  final int maximum;

  @override
  Widget build(BuildContext context, WidgetRef ref) => GridView.builder(
    padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
    gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
      maxCrossAxisExtent: 330,
      mainAxisExtent: 190,
      crossAxisSpacing: 14,
      mainAxisSpacing: 14,
    ),
    itemCount: categories.length,
    itemBuilder: (context, index) {
      final category = categories[index];
      final isSelected = selected.contains(category.id);
      final isDisabled =
          !category.eligible || (!isSelected && selected.length >= maximum);
      return _CategoryCard(
        category: category,
        selected: isSelected,
        disabled: isDisabled,
        icon: _icons[index % _icons.length],
        accent: _accents[index % _accents.length],
        onTap: isDisabled
            ? null
            : () => ref
                  .read(setupControllerProvider.notifier)
                  .toggle(category.id),
      );
    },
  );
}

const _icons = [
  Icons.account_balance_rounded,
  Icons.movie_filter_rounded,
  Icons.directions_car_filled_rounded,
  Icons.sports_soccer_rounded,
  Icons.public_rounded,
  Icons.science_rounded,
  Icons.restaurant_rounded,
  Icons.music_note_rounded,
];

const _accents = [
  FahmanColors.coral,
  FahmanColors.purple,
  FahmanColors.turquoise,
  FahmanColors.saffronDark,
];

class _CategoryCard extends StatelessWidget {
  const _CategoryCard({
    required this.category,
    required this.selected,
    required this.disabled,
    required this.icon,
    required this.accent,
    required this.onTap,
  });
  final CategoryAvailability category;
  final bool selected;
  final bool disabled;
  final IconData icon;
  final Color accent;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => Opacity(
    opacity: disabled ? 0.5 : 1,
    child: Material(
      color: selected ? FahmanColors.midnight : Colors.white,
      borderRadius: BorderRadius.circular(24),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(24),
        child: Container(
          padding: const EdgeInsets.all(17),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: selected ? FahmanColors.midnight : FahmanColors.line,
              width: 2,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 45,
                    height: 45,
                    decoration: BoxDecoration(
                      color: selected ? accent : accent.withValues(alpha: 0.14),
                      borderRadius: BorderRadius.circular(15),
                    ),
                    child: Icon(icon, color: selected ? Colors.white : accent),
                  ),
                  const Spacer(),
                  if (selected)
                    const Icon(
                      Icons.check_circle_rounded,
                      color: FahmanColors.saffron,
                    ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                category.name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: selected ? Colors.white : FahmanColors.ink,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                category.description,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: selected ? Colors.white70 : FahmanColors.muted,
                ),
              ),
              const Spacer(),
              Text(
                '${category.totalUnused} سؤال متاح',
                style: TextStyle(
                  color: selected ? FahmanColors.saffron : accent,
                  fontWeight: FontWeight.w800,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ),
    ),
  );
}

class _LoadError extends StatelessWidget {
  const _LoadError({required this.onRetry});
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(
          Icons.cloud_off_rounded,
          size: 52,
          color: FahmanColors.coral,
        ),
        const SizedBox(height: 12),
        const Text('تعذر تحميل الفئات'),
        TextButton(onPressed: onRetry, child: const Text('حاول مرة أخرى')),
      ],
    ),
  );
}
