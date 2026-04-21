class ApiConstants {
  ApiConstants._();

  // Override at build time:
  //   flutter build web --dart-define=CLOCKLY_API_BASE_URL=https://api.your-domain.com/api/v1
  // The HTTP default is intentional for local development only.
  // In release builds a non-HTTPS URL will trigger the assert below.
  static const String baseUrl = String.fromEnvironment(
    'CLOCKLY_API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000/api/v1',
  );

  // Fail fast in release mode if someone ships with an insecure URL.
  static void assertSecure() {
    assert(
      baseUrl.startsWith('https://') || baseUrl.startsWith('http://127.') || baseUrl.startsWith('http://localhost'),
      'CLOCKLY_API_BASE_URL must use HTTPS in production. Current value: $baseUrl',
    );
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
