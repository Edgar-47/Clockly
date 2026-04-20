class ApiConstants {
  ApiConstants._();

  static const String baseUrl = String.fromEnvironment(
    'CLOCKLY_API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8001/api/v1',
  );

  // Auth
  static const String login = '/auth/login/';
  static const String logout = '/auth/logout/';
  static const String me = '/auth/me/';
  static const String switchBusiness = '/auth/switch-business/';

  // Attendance
  static const String attendanceStatus = '/attendance/status/';
  static const String attendanceClockIn = '/attendance/clock-in/';
  static const String attendanceClockOut = '/attendance/clock-out/';
  static const String attendanceHistory = '/attendance/history/';
  static const String attendanceSessions = '/attendance/sessions/';

  // Employees
  static const String employees = '/employees/';

  // Business
  static const String businesses = '/businesses/';

  // Tickets
  static const String tickets = '/tickets/';

  // Dashboard
  static const String dashboardMetrics = '/dashboard/metrics/';

  // Subscriptions
  static const String subscriptions = '/subscriptions/';
  static const String plans = '/subscriptions/plans/';
}
