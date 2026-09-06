import 'package:fahman/app/router.dart';
import 'package:fahman/core/theme/app_theme.dart';
import 'package:flutter/material.dart';

class FahmanApp extends StatelessWidget {
  const FahmanApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp.router(
    title: 'فهمان',
    debugShowCheckedModeBanner: false,
    theme: FahmanTheme.light,
    locale: const Locale('ar'),
    builder: (context, child) => Directionality(
      textDirection: TextDirection.rtl,
      child: child ?? const SizedBox.shrink(),
    ),
    routerConfig: appRouter,
  );
}
