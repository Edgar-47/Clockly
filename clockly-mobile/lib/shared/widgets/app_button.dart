import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';

enum AppButtonVariant { primary, secondary, danger, ghost }

class AppButton extends StatelessWidget {
  const AppButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.loading = false,
    this.icon,
    this.variant = AppButtonVariant.primary,
    this.fullWidth = true,
    this.size = AppButtonSize.medium,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool loading;
  final IconData? icon;
  final AppButtonVariant variant;
  final bool fullWidth;
  final AppButtonSize size;

  @override
  Widget build(BuildContext context) {
    final height = switch (size) {
      AppButtonSize.small => 40.0,
      AppButtonSize.medium => 54.0,
      AppButtonSize.large => 62.0,
    };
    final fontSize = switch (size) {
      AppButtonSize.small => 13.0,
      AppButtonSize.medium => 15.0,
      AppButtonSize.large => 16.0,
    };

    final child = loading
        ? SizedBox(
            height: 20,
            width: 20,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: _foreground,
            ),
          )
        : Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (icon != null) ...[
                Icon(icon, size: fontSize + 2, color: _foreground),
                const SizedBox(width: 8),
              ],
              Text(
                label,
                style: TextStyle(
                  fontSize: fontSize,
                  fontWeight: FontWeight.w600,
                  color: _foreground,
                ),
              ),
            ],
          );

    final style = FilledButton.styleFrom(
      backgroundColor: _background,
      foregroundColor: _foreground,
      minimumSize: Size(fullWidth ? double.infinity : 0, height),
      elevation: 0,
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    );

    return switch (variant) {
      AppButtonVariant.ghost => TextButton(
          onPressed: loading ? null : onPressed,
          style: TextButton.styleFrom(
            foregroundColor: _foreground,
            minimumSize: Size(fullWidth ? double.infinity : 0, height),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          ),
          child: child,
        ),
      AppButtonVariant.secondary => OutlinedButton(
          onPressed: loading ? null : onPressed,
          style: OutlinedButton.styleFrom(
            foregroundColor: _foreground,
            side: const BorderSide(color: AppColors.neutral200),
            backgroundColor: AppColors.card,
            minimumSize: Size(fullWidth ? double.infinity : 0, height),
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          ),
          child: child,
        ),
      _ => FilledButton(
          onPressed: loading ? null : onPressed,
          style: style,
          child: child,
        ),
    };
  }

  Color? get _background => switch (variant) {
        AppButtonVariant.primary => AppColors.primary,
        AppButtonVariant.danger => AppColors.error,
        AppButtonVariant.secondary => AppColors.card,
        AppButtonVariant.ghost => Colors.transparent,
      };

  Color? get _foreground => switch (variant) {
        AppButtonVariant.primary => Colors.white,
        AppButtonVariant.danger => Colors.white,
        AppButtonVariant.secondary => AppColors.primary,
        AppButtonVariant.ghost => AppColors.cobaltLight,
      };
}

enum AppButtonSize { small, medium, large }
