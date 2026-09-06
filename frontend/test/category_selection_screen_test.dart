import 'package:fahman/core/theme/app_theme.dart';
import 'package:fahman/features/match_setup/presentation/category_selection_screen.dart';
import 'package:fahman/features/match_setup/presentation/setup_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

void main() {
  testWidgets(
    'shows categories without overflowing on a short landscape phone',
    (tester) async {
      tester.view.physicalSize = const Size(800, 360);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final router = GoRouter(
        initialLocation: '/setup/categories',
        routes: [
          GoRoute(
            path: '/setup/categories',
            builder: (context, state) => const CategorySelectionScreen(),
          ),
          GoRoute(
            path: '/home',
            builder: (context, state) => const SizedBox.shrink(),
          ),
          GoRoute(
            path: '/setup/teams',
            builder: (context, state) => const SizedBox.shrink(),
          ),
        ],
      );
      addTearDown(router.dispose);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            categoriesProvider.overrideWith((ref) async => demoCategories),
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
      expect(find.byType(GridView), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
