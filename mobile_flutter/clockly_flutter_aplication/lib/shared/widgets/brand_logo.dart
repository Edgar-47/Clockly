import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../../core/theme/app_colors.dart';

enum ClocklyLogoVariant { horizontal, vertical, mark }

class ClocklyBrandLogo extends StatelessWidget {
  const ClocklyBrandLogo({
    super.key,
    this.variant = ClocklyLogoVariant.horizontal,
    this.markSize = 34,
    this.wordmarkSize = 24,
    this.inverse = false,
  });

  final ClocklyLogoVariant variant;
  final double markSize;
  final double wordmarkSize;
  final bool inverse;

  static const _markAsset = 'assets/brand/clockly-flow-icon.svg';

  @override
  Widget build(BuildContext context) {
    final textColor = inverse ? Colors.white : AppColors.textPrimary;
    final mark = _ClocklyMark(size: markSize, inverse: inverse);

    if (variant == ClocklyLogoVariant.mark) {
      return mark;
    }

    final wordmark = Text(
      'ClockLy',
      style: TextStyle(
        color: textColor,
        fontSize: wordmarkSize,
        fontWeight: FontWeight.w600,
        letterSpacing: 0,
        height: 1,
      ),
    );

    final children = <Widget>[
      mark,
      SizedBox(
        width: variant == ClocklyLogoVariant.horizontal ? 10 : 0,
        height: 8,
      ),
      wordmark,
    ];

    return Semantics(
      label: 'ClockLy',
      image: true,
      child: ExcludeSemantics(
        child: variant == ClocklyLogoVariant.horizontal
            ? Row(mainAxisSize: MainAxisSize.min, children: children)
            : Column(mainAxisSize: MainAxisSize.min, children: children),
      ),
    );
  }
}

class _ClocklyMark extends StatelessWidget {
  const _ClocklyMark({required this.size, required this.inverse});

  final double size;
  final bool inverse;

  @override
  Widget build(BuildContext context) {
    return SvgPicture.asset(
      ClocklyBrandLogo._markAsset,
      width: size,
      height: size,
      colorFilter: inverse
          ? const ColorFilter.mode(Colors.white, BlendMode.srcIn)
          : null,
      semanticsLabel: 'ClockLy',
    );
  }
}
