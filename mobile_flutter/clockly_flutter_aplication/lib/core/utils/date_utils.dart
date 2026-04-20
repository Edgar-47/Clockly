import 'package:intl/intl.dart';

class AppDateUtils {
  AppDateUtils._();

  static String formatDate(DateTime dt) => DateFormat('dd/MM/yyyy').format(dt);
  static String formatTime(DateTime dt) => DateFormat('HH:mm').format(dt);
  static String formatDateTime(DateTime dt) => DateFormat('dd/MM/yyyy HH:mm').format(dt);
  static String formatDateLong(DateTime dt) => DateFormat('EEEE, d MMMM yyyy', 'es').format(dt);
  static String formatMonthYear(DateTime dt) => DateFormat('MMMM yyyy', 'es').format(dt);

  static String formatDuration(int totalSeconds) {
    if (totalSeconds <= 0) return '0h 0m';
    final h = totalSeconds ~/ 3600;
    final m = (totalSeconds % 3600) ~/ 60;
    if (h == 0) return '${m}m';
    if (m == 0) return '${h}h';
    return '${h}h ${m}m';
  }

  static String formatDurationVerbose(int totalSeconds) {
    final h = totalSeconds ~/ 3600;
    final m = (totalSeconds % 3600) ~/ 60;
    final s = totalSeconds % 60;
    return '${h.toString().padLeft(2, '0')}:${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }

  static String timeAgo(DateTime dt) {
    final now = DateTime.now();
    final diff = now.difference(dt);
    if (diff.inSeconds < 60) return 'Hace un momento';
    if (diff.inMinutes < 60) return 'Hace ${diff.inMinutes}m';
    if (diff.inHours < 24) return 'Hace ${diff.inHours}h';
    if (diff.inDays < 7) return 'Hace ${diff.inDays}d';
    return formatDate(dt);
  }

  static bool isSameDay(DateTime a, DateTime b) {
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }

  static bool isToday(DateTime dt) => isSameDay(dt, DateTime.now());

  static DateTime startOfDay(DateTime dt) => DateTime(dt.year, dt.month, dt.day);
  static DateTime endOfDay(DateTime dt) => DateTime(dt.year, dt.month, dt.day, 23, 59, 59);
  static DateTime startOfWeek(DateTime dt) {
    final monday = dt.subtract(Duration(days: dt.weekday - 1));
    return startOfDay(monday);
  }

  static DateTime startOfMonth(DateTime dt) => DateTime(dt.year, dt.month, 1);
}
