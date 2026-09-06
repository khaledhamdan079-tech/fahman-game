import 'package:flutter/material.dart';

abstract final class FahmanColors {
  static const midnight = Color(0xFF101A35);
  static const midnightSoft = Color(0xFF18264A);
  static const cream = Color(0xFFFFF8E7);
  static const saffron = Color(0xFFFFC83D);
  static const saffronDark = Color(0xFFE7A900);
  static const coral = Color(0xFFFF6B4A);
  static const turquoise = Color(0xFF27C7A8);
  static const purple = Color(0xFF7159D9);
  static const ink = Color(0xFF18213A);
  static const muted = Color(0xFF687087);
  static const line = Color(0xFFE8E2D4);
}

abstract final class FahmanTheme {
  static ThemeData get light {
    const scheme = ColorScheme.light(
      primary: FahmanColors.midnight,
      onPrimary: Colors.white,
      secondary: FahmanColors.saffron,
      onSecondary: FahmanColors.ink,
      tertiary: FahmanColors.turquoise,
      error: FahmanColors.coral,
      surface: FahmanColors.cream,
      onSurface: FahmanColors.ink,
    );

    final base = ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: FahmanColors.cream,
      fontFamilyFallback: const ['Noto Kufi Arabic', 'Tahoma', 'Arial'],
    );

    return base.copyWith(
      textTheme: base.textTheme.copyWith(
        displayLarge: const TextStyle(
          fontSize: 54,
          fontWeight: FontWeight.w900,
          height: 1.05,
          letterSpacing: -1.5,
          color: FahmanColors.midnight,
        ),
        headlineLarge: const TextStyle(
          fontSize: 30,
          fontWeight: FontWeight.w900,
          height: 1.25,
          color: FahmanColors.midnight,
        ),
        headlineMedium: const TextStyle(
          fontSize: 23,
          fontWeight: FontWeight.w800,
          color: FahmanColors.midnight,
        ),
        titleLarge: const TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w800,
          color: FahmanColors.ink,
        ),
        bodyLarge: const TextStyle(
          fontSize: 16,
          height: 1.65,
          color: FahmanColors.ink,
        ),
        bodyMedium: const TextStyle(
          fontSize: 14,
          height: 1.55,
          color: FahmanColors.muted,
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        foregroundColor: FahmanColors.midnight,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: FahmanColors.midnight,
          fontSize: 20,
          fontWeight: FontWeight.w900,
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: FahmanColors.midnight,
          foregroundColor: Colors.white,
          minimumSize: const Size(0, 56),
          padding: const EdgeInsets.symmetric(horizontal: 26, vertical: 15),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: FahmanColors.midnight,
          minimumSize: const Size(0, 54),
          side: const BorderSide(color: FahmanColors.line, width: 1.5),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 18,
          vertical: 17,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: const BorderSide(color: FahmanColors.line),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: const BorderSide(color: FahmanColors.line),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: const BorderSide(
            color: FahmanColors.saffronDark,
            width: 2,
          ),
        ),
      ),
    );
  }
}
