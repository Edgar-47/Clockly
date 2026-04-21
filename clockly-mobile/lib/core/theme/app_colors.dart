import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  // ClockLy premium tokens
  static const Color ink = Color(0xFF06091A);
  static const Color ink2 = Color(0xFF0B1026);
  static const Color ink3 = Color(0xFF121A35);
  static const Color inkMuted = Color(0xFF7F8AA8);

  static const Color paper = Color(0xFFFAFAF7);
  static const Color paper2 = Color(0xFFF2F5FA);
  static const Color card = Color(0xFFFFFFFF);
  static const Color cardMuted = Color(0xFFF7F8FC);

  static const Color cobalt = Color(0xFF2F5BFF);
  static const Color cobaltDark = Color(0xFF2147D8);
  static const Color cobaltSoft = Color(0xFFE8EEFF);
  static const Color cobaltLight = Color(0xFF8EA6FF);

  static const Color verde = Color(0xFF1FBF75);
  static const Color verdeSoft = Color(0xFFEAFBF2);
  static const Color amber = Color(0xFFF6A21A);
  static const Color amberSoft = Color(0xFFFFF4DB);
  static const Color rose = Color(0xFFF04468);
  static const Color roseSoft = Color(0xFFFFEEF2);

  // Compatibility aliases used by existing screens and widgets.
  static const Color primary = cobalt;
  static const Color primaryDark = cobaltDark;
  static const Color primaryLight = cobaltLight;
  static const Color primarySurface = cobaltSoft;

  static const Color accent = Color(0xFF7C5CFF);
  static const Color accentLight = Color(0xFFEDE9FF);

  static const Color success = verde;
  static const Color successLight = verdeSoft;
  static const Color warning = amber;
  static const Color warningLight = amberSoft;
  static const Color error = rose;
  static const Color errorLight = roseSoft;
  static const Color info = Color(0xFF0EA5E9);
  static const Color infoLight = Color(0xFFEAF6FF);

  static const Color neutral50 = Color(0xFFF8FAFC);
  static const Color neutral100 = Color(0xFFF1F5F9);
  static const Color neutral200 = Color(0xFFE4E8F0);
  static const Color neutral300 = Color(0xFFD1D7E5);
  static const Color neutral400 = Color(0xFF98A2B3);
  static const Color neutral500 = Color(0xFF667085);
  static const Color neutral600 = Color(0xFF475467);
  static const Color neutral700 = Color(0xFF344054);
  static const Color neutral800 = Color(0xFF1D2939);
  static const Color neutral900 = ink;

  static const Color background = paper2;
  static const Color surface = card;
  static const Color surfaceVariant = paper2;

  static const Color textPrimary = Color(0xFF121826);
  static const Color textSecondary = Color(0xFF596275);
  static const Color textHint = Color(0xFF98A2B3);
  static const Color textDisabled = Color(0xFFC9D0DD);
  static const Color textInverse = paper;

  static const Color clockedIn = verde;
  static const Color clockedOut = neutral400;
  static const Color onBreak = amber;

  static const Color planFree = neutral500;
  static const Color planPro = cobalt;
  static const Color planEnterprise = Color(0xFF7C5CFF);
}
