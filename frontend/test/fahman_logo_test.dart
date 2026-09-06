import 'package:fahman/core/theme/app_theme.dart';
import 'package:fahman/shared/widgets/fahman_logo.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('renders the Arabic game identity', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: FahmanTheme.light,
        home: const Scaffold(body: FahmanLogo()),
      ),
    );

    expect(find.text('فهمان'), findsOneWidget);
    expect(find.byIcon(Icons.psychology_alt_rounded), findsOneWidget);
  });
}
