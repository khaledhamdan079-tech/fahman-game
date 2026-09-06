import 'package:fahman/core/theme/app_theme.dart';
import 'package:flutter/material.dart';

class FahmanLogo extends StatelessWidget {
  const FahmanLogo({super.key, this.compact = false, this.light = false});

  final bool compact;
  final bool light;

  @override
  Widget build(BuildContext context) {
    final foreground = light ? Colors.white : FahmanColors.midnight;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: compact ? 42 : 58,
          height: compact ? 42 : 58,
          decoration: BoxDecoration(
            color: FahmanColors.saffron,
            borderRadius: BorderRadius.circular(compact ? 14 : 19),
            boxShadow: const [
              BoxShadow(
                color: Color(0x33000000),
                blurRadius: 0,
                offset: Offset(0, 5),
              ),
            ],
          ),
          child: Icon(
            Icons.psychology_alt_rounded,
            color: FahmanColors.midnight,
            size: compact ? 28 : 39,
          ),
        ),
        const SizedBox(width: 12),
        Text(
          'فهمان',
          style: TextStyle(
            color: foreground,
            fontSize: compact ? 27 : 42,
            fontWeight: FontWeight.w900,
            height: 1,
          ),
        ),
      ],
    );
  }
}
