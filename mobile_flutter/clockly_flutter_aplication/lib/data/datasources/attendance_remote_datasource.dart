import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';
import '../models/attendance/attendance_session_model.dart';

class AttendanceRemoteDatasource {
  const AttendanceRemoteDatasource(this._client);

  final ApiClient _client;

  Future<List<AttendanceStatusModel>> getStatus() async {
    // Backend returns {"items": [...]} from GET /attendance
    final data = await _client.get(ApiConstants.attendanceStatus) as Map<String, dynamic>;
    final items = data['items'] as List<dynamic>? ?? [];
    return items
        .map((e) => AttendanceStatusModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<AttendanceSessionModel> clockIn({
    double? lat,
    double? lng,
    double? accuracy,
  }) async {
    // Backend ClockRequest only accepts: employee_id, exit_note, incident_type
    // Location fields are not in the schema — omit them to avoid 400
    final data = await _client.post(ApiConstants.attendanceClockIn, body: {})
        as Map<String, dynamic>;
    // Backend wraps session: {"session": {...}}
    final sessionData = data['session'] as Map<String, dynamic>? ?? data;
    return AttendanceSessionModel.fromJson(sessionData);
  }

  Future<AttendanceSessionModel> clockOut({
    String? notes,
    String? incidentType,
    double? lat,
    double? lng,
    double? accuracy,
  }) async {
    final body = <String, dynamic>{
      if (notes != null && notes.isNotEmpty) 'exit_note': notes,
      if (incidentType != null) 'incident_type': incidentType,
    };
    final data = await _client.post(ApiConstants.attendanceClockOut, body: body)
        as Map<String, dynamic>;
    // Backend wraps session: {"session": {...}}
    final sessionData = data['session'] as Map<String, dynamic>? ?? data;
    return AttendanceSessionModel.fromJson(sessionData);
  }

  Future<List<AttendanceSessionModel>> getHistory({
    String? businessId,
    int? userId,
    DateTime? from,
    DateTime? to,
    int page = 1,
  }) async {
    final params = <String, String>{
      if (from != null) 'date_from': from.toIso8601String().split('T').first,
      if (to != null) 'date_to': to.toIso8601String().split('T').first,
      if (userId != null) 'employee_id': userId.toString(),
    };
    final data = await _client.get(ApiConstants.attendanceHistory, queryParams: params);
    // Backend returns {"items": [...]}
    final list = data is List ? data : (data as Map<String, dynamic>)['items'] as List? ?? [];
    return list
        .map((e) => AttendanceSessionModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<AttendanceSessionModel> adminCloseSession({
    required int sessionId,
    required String reason,
  }) async {
    final data = await _client.patch(
      '${ApiConstants.attendanceSessions}$sessionId/',
      body: {
        'status': 'manual_close',
        'closed_by_admin_reason': reason,
        'clock_out': DateTime.now().toIso8601String(),
      },
    ) as Map<String, dynamic>;
    return AttendanceSessionModel.fromJson(data);
  }
}
