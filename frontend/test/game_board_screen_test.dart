import 'package:fahman/core/theme/app_theme.dart';
import 'package:fahman/features/game/game_board_screen.dart';
import 'package:fahman/features/match_setup/domain/match_snapshot.dart';
import 'package:fahman/features/match_setup/presentation/setup_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

class _BoardTestController extends SetupController {
  @override
  SetupState build() => SetupState(
    activeMatch: MatchSnapshot.demo(
      categories: const [
        CategoryAvailabilityReference(id: 'history', name: 'تاريخنا'),
        CategoryAvailabilityReference(id: 'cinema', name: 'سينما وشاشة'),
        CategoryAvailabilityReference(id: 'cars', name: 'عالم السيارات'),
      ],
      teamOne: 'الصقور',
      teamTwo: 'الأبطال',
    ),
  );
}

void main() {
  testWidgets('keeps all question rows usable on a landscape phone', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(800, 360);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final router = GoRouter(
      initialLocation: '/game',
      routes: [
        GoRoute(
          path: '/game',
          builder: (context, state) => const GameBoardScreen(),
        ),
        GoRoute(
          path: '/home',
          builder: (context, state) => const SizedBox.shrink(),
        ),
        GoRoute(
          path: '/question',
          builder: (context, state) => const SizedBox.shrink(),
        ),
      ],
    );
    addTearDown(router.dispose);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          setupControllerProvider.overrideWith(_BoardTestController.new),
        ],
        child: MaterialApp.router(
          theme: FahmanTheme.light,
          locale: const Locale('ar'),
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(
              context,
            ).copyWith(padding: const EdgeInsets.only(bottom: 24)),
            child: Directionality(
              textDirection: TextDirection.rtl,
              child: child ?? const SizedBox.shrink(),
            ),
          ),
          routerConfig: router,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('تاريخنا'), findsOneWidget);
    expect(find.text('200'), findsNWidgets(6));
    final firstQuestion = find.ancestor(
      of: find.text('200').first,
      matching: find.byType(InkWell),
    );
    expect(
      tester.getSize(firstQuestion.first).height,
      greaterThanOrEqualTo(24),
    );
    expect(tester.takeException(), isNull);

    await tester.tap(find.text('400').first);
    await tester.pumpAndSettle();

    expect(find.text('سؤال بـ 400 نقطة'), findsOneWidget);
    expect(find.text('افتح السؤال'), findsOneWidget);
    expect(find.text('دبل النقاط ثم افتح'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
