import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';
import '../models/attendance/attendance_session_model.dart';

class AttendanceRemoteDatasource {
  const AttendanceRemoteDatasource(this._client);

  final ApiClient _client;

  Future<List<AttendanceStatusModel>> getStatus() async {
    final data = await _client.get(ApiConstants.attendanceStatus);
    if (data is List) {
      return data
          .map((e) => AttendanceStatusModel.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    final single = AttendanceStatusModel.fromJson(data as Map<String, dynamic>);
    return [single];
  }

  Future<AttendanceSessionModel> clockIn({
    double? lat,
    double? lng,
    double? accuracy,
  }) async {
    final body = <String, dynamic>{
      'method': 'app',
      if (lat != null) 'location_lat': lat,
      if (lng != null) 'location_lng': lng,
      if (accuracy != null) 'location_accuracy': accuracy,
    };
    final data = await _client.post(ApiConstants.attendanceClockIn, body: body)
        as Map<String, dynamic>;
    return AttendanceSessionModel.fromJson(data);
  }

  Future<AttendanceSessionModel> clockOut({
    String? notes,
    String? incidentType,
    double? lat,
    double? lng,
    double? accuracy,
  }) async {
    final body = <String, dynamic>{
      if (notes != null && notes.isNotEmpty) 'notes': notes,
      if (incidentType != null) 'incident_type': incidentType,
      if (lat != null) 'location_lat': lat,
      if (lng != null) 'location_lng': lng,
      if (accuracy != null) 'location_accuracy': accuracy,
    };
    final data = await _client.post(ApiConstants.attendanceClockOut, body: body)
        as Map<String, dynamic>;
    return AttendanceSessionModel.fromJson(data);
  }

  Future<List<AttendanceSessionModel>> getHistory({
    String? businessId,
    int? userId,
    DateTime? from,
    DateTime? to,
    int page = 1,
  }) async {
    final params = <String, String>{
      'page': page.toString(),
      if (businessId != null) 'business_id': businessId,
      if (userId != null) 'user_id': userId.toString(),
      if (from != null) 'from': from.toIso8601String().split('T').first,
      if (to != null) 'to': to.toIso8601String().split('T').first,
    };
    final data = await _client.get(ApiConstants.attendanceHistory, queryParams: params);
    final list = data is List ? data : (data as Map<String, dynamic>)['results'] as List? ?? [];
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
