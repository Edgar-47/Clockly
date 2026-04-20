import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

class UserAvatar extends StatelessWidget {
  const UserAvatar({
    super.key,
    required this.initials,
    this.imageUrl,
    this.size = 40,
    this.color,
  });

  final String initials;
  final String? imageUrl;
  final double size;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final bgColor = color ?? AppColors.primary;
    return CircleAvatar(
      radius: size / 2,
      backgroundColor: bgColor.withOpacity(0.15),
      backgroundImage: imageUrl != null ? NetworkImage(imageUrl!) : null,
      child: imageUrl == null
          ? Text(
              initials,
              style: TextStyle(
                fontSize: size * 0.35,
                fontWeight: FontWeight.w700,
                color: bgColor,
              ),
            )
          : null,
    );
  }
}
