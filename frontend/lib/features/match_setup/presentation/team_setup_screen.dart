import 'package:fahman/core/theme/app_theme.dart';
import 'package:fahman/features/match_setup/domain/category_availability.dart';
import 'package:fahman/features/match_setup/presentation/setup_controller.dart';
import 'package:fahman/shared/widgets/game_background.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class TeamSetupScreen extends ConsumerStatefulWidget {
  const TeamSetupScreen({super.key});

  @override
  ConsumerState<TeamSetupScreen> createState() => _TeamSetupScreenState();
}

class _TeamSetupScreenState extends ConsumerState<TeamSetupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _teamOne = TextEditingController(text: 'الصقور');
  final _teamTwo = TextEditingController(text: 'الأبطال');

  @override
  void dispose() {
    _teamOne.dispose();
    _teamTwo.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final setup = ref.watch(setupControllerProvider);
    final categoryState = ref.watch(categoriesProvider);
    final categories = switch (categoryState) {
      AsyncData(:final value) => value,
      _ => const <CategoryAvailability>[],
    };
    return Scaffold(
      appBar: AppBar(
        title: const Text('الفريقان'),
        leading: IconButton(
          onPressed: () => context.go('/setup/categories'),
          icon: const Icon(Icons.arrow_forward_rounded),
        ),
      ),
      body: GameBackground(
        child: SafeArea(
          top: false,
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(22),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 720),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'سمِّ المنافسين',
                        style: Theme.of(context).textTheme.headlineLarge,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'كل فريق يملك المساعدات الثلاث مرة واحدة.',
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                      const SizedBox(height: 25),
                      _TeamField(
                        controller: _teamOne,
                        label: 'الفريق الأول',
                        icon: Icons.flight_rounded,
                        color: FahmanColors.coral,
                      ),
                      const SizedBox(height: 14),
                      _TeamField(
                        controller: _teamTwo,
                        label: 'الفريق الثاني',
                        icon: Icons.shield_rounded,
                        color: FahmanColors.purple,
                      ),
                      const SizedBox(height: 22),
                      const _LifelineSummary(),
                      if (setup.error != null) ...[
                        const SizedBox(height: 14),
                        Text(
                          setup.error!,
                          style: const TextStyle(
                            color: FahmanColors.coral,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ],
                      const SizedBox(height: 22),
                      FilledButton.icon(
                        onPressed: setup.isCreating
                            ? null
                            : () async {
                                if (!_formKey.currentState!.validate()) return;
                                final success = await ref
                                    .read(setupControllerProvider.notifier)
                                    .startMatch(
                                      allCategories: categories,
                                      teamOne: _teamOne.text.trim(),
                                      teamTwo: _teamTwo.text.trim(),
                                    );
                                if (success && context.mounted) {
                                  context.go('/game');
                                }
                              },
                        icon: setup.isCreating
                            ? const SizedBox.square(
                                dimension: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.rocket_launch_rounded),
                        label: Text(
                          setup.isCreating ? 'نجهّز الأسئلة…' : 'ابدأ الجولة',
                        ),
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

class _TeamField extends StatelessWidget {
  const _TeamField({
    required this.controller,
    required this.label,
    required this.icon,
    required this.color,
  });
  final TextEditingController controller;
  final String label;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) => TextFormField(
    controller: controller,
    maxLength: 30,
    textInputAction: TextInputAction.next,
    decoration: InputDecoration(
      labelText: label,
      counterText: '',
      prefixIcon: Icon(icon, color: color),
    ),
    validator: (value) =>
        value == null || value.trim().isEmpty ? 'اكتب اسم الفريق' : null,
  );
}

class _LifelineSummary extends StatelessWidget {
  const _LifelineSummary();

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(18),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(22),
      border: Border.all(color: FahmanColors.line),
    ),
    child: const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'مساعدات كل فريق',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900),
        ),
        SizedBox(height: 13),
        Wrap(
          spacing: 9,
          runSpacing: 9,
          children: [
            _RuleChip(icon: Icons.looks_two_rounded, text: 'إجابتان'),
            _RuleChip(icon: Icons.exposure_plus_2_rounded, text: 'دبل النقاط'),
            _RuleChip(icon: Icons.block_rounded, text: 'حجب الخصم'),
          ],
        ),
      ],
    ),
  );
}

class _RuleChip extends StatelessWidget {
  const _RuleChip({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
    decoration: BoxDecoration(
      color: FahmanColors.cream,
      borderRadius: BorderRadius.circular(999),
    ),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 18, color: FahmanColors.purple),
        const SizedBox(width: 6),
        Text(text, style: const TextStyle(fontWeight: FontWeight.w800)),
      ],
    ),
  );
}
