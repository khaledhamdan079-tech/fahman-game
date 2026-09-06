import 'package:fahman/core/theme/app_theme.dart';
import 'package:flutter/material.dart';

class GameBackground extends StatelessWidget {
  const GameBackground({required this.child, super.key, this.dark = false});

  final Widget child;
  final bool dark;

  @override
  Widget build(BuildContext context) {
    final background = dark ? FahmanColors.midnight : FahmanColors.cream;
    return ColoredBox(
      color: background,
      child: Stack(
        children: [
          Positioned(
            top: -90,
            left: -70,
            child: _Bubble(
              size: 230,
              color: FahmanColors.saffron.withValues(alpha: dark ? 0.12 : 0.22),
            ),
          ),
          Positioned(
            right: -90,
            bottom: 60,
            child: _Bubble(
              size: 260,
              color: FahmanColors.turquoise.withValues(
                alpha: dark ? 0.10 : 0.15,
              ),
            ),
          ),
          Positioned.fill(child: child),
        ],
      ),
    );
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble({required this.size, required this.color});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) => Container(
    width: size,
    height: size,
    decoration: BoxDecoration(color: color, shape: BoxShape.circle),
  );
}
