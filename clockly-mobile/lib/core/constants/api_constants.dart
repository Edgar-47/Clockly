import 'package:flutter/foundation.dart';

class ApiConstants {
  ApiConstants._();

  // Override at build time:
  //   flutter run --dart-define=CLOCKLY_API_BASE_URL=http://127.0.0.1:8000/api/v1
  //   flutter build apk --dart-define=CLOCKLY_API_BASE_URL=https://your-domain.example/api/v1
  // The HTTP default is intentional for local development only.
  static const String baseUrl = String.fromEnvironment(
    'CLOCKLY_API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000/api/v1',
  );

  static void validateBaseUrl() {
    assert(
      baseUrl.startsWith('https://') ||
          baseUrl.startsWith('http://127.') ||
          baseUrl.startsWith('http://localhost') ||
          baseUrl.startsWith('http://10.0.2.2'),
      'CLOCKLY_API_BASE_URL must use HTTPS in production. Current value: $baseUrl',
    );
    if (kReleaseMode && !baseUrl.startsWith('https://')) {
      throw StateError('CLOCKLY_API_BASE_URL must use HTTPS in release builds.');
    }
  }

  // Auth
  static const String login = '/auth/login';
  static const String logout = '/auth/logout';
  static const String me = '/auth/me';
  // Switch business lives under /businesses, not /auth
  static const String switchBusiness = '/businesses/switch';

  // Attendance — backend exposes /attendance (no /status sub-path)
  static const String attendanceStatus = '/attendance';
  static const String attendanceClockIn = '/attendance/clock-in';
  static const String attendanceClockOut = '/attendance/clock-out';
  static const String attendanceHistory = '/attendance/history';
  static const String attendanceSessions = '/attendance/sessions';

  // Employees
  static const String employees = '/employees';

  // Business
  static const String businesses = '/businesses';

  // Tickets (maps to backend /expenses)
  static const String tickets = '/tickets';

  // Dashboard — backend exposes /dashboard/summary, not /dashboard/metrics
  static const String dashboardMetrics = '/dashboard/summary';

  // Subscriptions (not yet implemented in backend)
  static const String subscriptions = '/subscriptions';
  static const String plans = '/subscriptions/plans';
}
