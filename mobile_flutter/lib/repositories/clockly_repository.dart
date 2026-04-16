import '../core/network/api_client.dart';
import '../core/storage/session_storage.dart';
import '../models/attendance.dart';
import '../models/auth_session.dart';
import '../services/attendance_service.dart';
import '../services/auth_service.dart';
import '../services/business_service.dart';

class ClocklyRepository {
  ClocklyRepository({
    required ApiClient apiClient,
    required SessionStorage sessionStorage,
  })  : _apiClient = apiClient,
        _sessionStorage = sessionStorage,
        _authService = AuthService(apiClient),
        _businessService = BusinessService(apiClient),
        _attendanceService = AttendanceService(apiClient);

  final ApiClient _apiClient;
  final SessionStorage _sessionStorage;
  final AuthService _authService;
  final BusinessService _businessService;
  final AttendanceService _attendanceService;

  Future<AuthSession?> restoreSession() async {
    final token = await _sessionStorage.readToken();
    if (token == null || token.isEmpty) return null;
    _apiClient.setAccessToken(token);
    final session = await _authService.me();
    await _sessionStorage.saveToken(session.accessToken);
    return session;
  }

  Future<AuthSession> login(String identifier, String password) async {
    final session = await _authService.login(
      identifier: identifier,
      password: password,
    );
    await _sessionStorage.saveToken(session.accessToken);
    return session;
  }

  Future<AuthSession> switchBusiness(String businessId) async {
    final session = await _businessService.switchBusiness(businessId);
    await _sessionStorage.saveToken(session.accessToken);
    return session;
  }

  Future<List<AttendanceStatus>> currentAttendance() {
    return _attendanceService.currentStatus();
  }

  Future<AttendanceSession> clockIn() {
    return _attendanceService.clockIn();
  }

  Future<AttendanceSession> clockOut({String? exitNote, String? incidentType}) {
    return _attendanceService.clockOut(
      exitNote: exitNote,
      incidentType: incidentType,
    );
  }

  Future<List<AttendanceSession>> history() {
    return _attendanceService.history();
  }

  Future<void> logout() async {
    await _authService.logout();
    await _sessionStorage.clear();
  }
}
