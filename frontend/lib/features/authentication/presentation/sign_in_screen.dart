import 'package:fahman/core/theme/app_theme.dart';
import 'package:fahman/features/authentication/presentation/auth_controller.dart';
import 'package:fahman/shared/widgets/fahman_logo.dart';
import 'package:fahman/shared/widgets/game_background.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class SignInScreen extends ConsumerStatefulWidget {
  const SignInScreen({super.key});

  @override
  ConsumerState<SignInScreen> createState() => _SignInScreenState();
}

class _SignInScreenState extends ConsumerState<SignInScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await ref.read(authControllerProvider.notifier).bootstrap();
      if (mounted && ref.read(authControllerProvider).hasAccess) {
        context.go('/home');
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final wide = MediaQuery.sizeOf(context).width >= 760;
    return Scaffold(
      body: GameBackground(
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1050),
                child: Flex(
                  direction: wide ? Axis.horizontal : Axis.vertical,
                  children: [
                    if (wide)
                      Expanded(flex: 6, child: _HeroCopy(wide: wide))
                    else
                      _HeroCopy(wide: wide),
                    SizedBox(width: wide ? 54 : 0, height: wide ? 0 : 34),
                    if (wide)
                      Expanded(flex: 4, child: _SignInCard(auth: auth))
                    else
                      _SignInCard(auth: auth),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _HeroCopy extends StatelessWidget {
  const _HeroCopy({required this.wide});
  final bool wide;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      const FahmanLogo(),
      const SizedBox(height: 32),
      Text(
        'جمّع فريقك،\nوخَلّ المعرفة تحكم.',
        style: Theme.of(
          context,
        ).textTheme.displayLarge?.copyWith(fontSize: wide ? 54 : 40),
      ),
      const SizedBox(height: 18),
      Text(
        'أسئلة عربية، تحديات بالصوت والصورة، وثلاث مساعدات تقلب نتيجة الجولة.',
        style: Theme.of(context).textTheme.bodyLarge,
      ),
      const SizedBox(height: 26),
      const Wrap(
        spacing: 10,
        runSpacing: 10,
        children: [
          _FeaturePill(icon: Icons.groups_2_rounded, label: 'فريقان'),
          _FeaturePill(icon: Icons.category_rounded, label: '٣–٧ فئات'),
          _FeaturePill(
            icon: Icons.emoji_events_rounded,
            label: 'نقاط ومساعدات',
          ),
        ],
      ),
    ],
  );
}

class _FeaturePill extends StatelessWidget {
  const _FeaturePill({required this.icon, required this.label});
  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(999),
      border: Border.all(color: FahmanColors.line),
    ),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 18, color: FahmanColors.purple),
        const SizedBox(width: 7),
        Text(label, style: const TextStyle(fontWeight: FontWeight.w800)),
      ],
    ),
  );
}

class _SignInCard extends ConsumerWidget {
  const _SignInCard({required this.auth});
  final AuthState auth;

  @override
  Widget build(BuildContext context, WidgetRef ref) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(26),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(28),
      border: Border.all(color: FahmanColors.line),
      boxShadow: const [
        BoxShadow(
          color: Color(0x180E1730),
          blurRadius: 28,
          offset: Offset(0, 14),
        ),
      ],
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'جاهز تثبت إنك فهمان؟',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 9),
        Text(
          'سجّل دخولك لنحفظ أسئلتك وجولاتك ونتائجك.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 24),
        FilledButton.icon(
          onPressed:
              auth.status == AuthStatus.busy ||
                  auth.status == AuthStatus.booting
              ? null
              : () async {
                  if (await ref
                          .read(authControllerProvider.notifier)
                          .signIn() &&
                      context.mounted) {
                    context.go('/home');
                  }
                },
          icon: auth.status == AuthStatus.busy
              ? const SizedBox.square(
                  dimension: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : const Icon(Icons.login_rounded),
          label: const Text('الدخول باستخدام Google'),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: auth.status == AuthStatus.busy
              ? null
              : () {
                  ref.read(authControllerProvider.notifier).continueAsDemo();
                  context.go('/home');
                },
          icon: const Icon(Icons.visibility_rounded),
          label: const Text('استعراض التصميم كتجربة'),
        ),
        if (auth.message != null) ...[
          const SizedBox(height: 16),
          Text(
            auth.message!,
            style: const TextStyle(
              color: FahmanColors.coral,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
        const SizedBox(height: 20),
        const Text(
          'بتسجيل الدخول أنت توافق على حفظ تاريخ اللعب والأسئلة المستخدمة.',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 11,
            color: FahmanColors.muted,
            height: 1.5,
          ),
        ),
      ],
    ),
  );
}
