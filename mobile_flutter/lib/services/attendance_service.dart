import '../core/network/api_client.dart';
import '../models/attendance.dart';

class AttendanceService {
  const AttendanceService(this._apiClient);

  final ApiClient _apiClient;

  Future<List<AttendanceStatus>> currentStatus() async {
    final json = await _apiClient.get('/attendance');
    final items = json['items'];
    if (items is! List) return const [];
    return items
        .whereType<Map<String, dynamic>>()
        .map(AttendanceStatus.fromJson)
        .toList();
  }

  Future<AttendanceSession> clockIn() async {
    final json = await _apiClient.post('/attendance/clock-in', body: {});
    return AttendanceSession.fromJson(json['session'] as Map<String, dynamic>);
  }

  Future<AttendanceSession> clockOut({String? exitNote, String? incidentType}) async {
    final json = await _apiClient.post('/attendance/clock-out', body: {
      if (exitNote != null && exitNote.isNotEmpty) 'exit_note': exitNote,
      if (incidentType != null && incidentType.isNotEmpty) 'incident_type': incidentType,
    });
    return AttendanceSession.fromJson(json['session'] as Map<String, dynamic>);
  }

  Future<List<AttendanceSession>> history() async {
    final json = await _apiClient.get('/attendance/history');
    final items = json['items'];
    if (items is! List) return const [];
    return items.whereType<Map<String, dynamic>>().map((item) {
      return AttendanceSession.fromJson({
        'id': item['id'],
        'business_id': item['business_id'],
        'user_id': item['user_id'],
        'clock_in_time': item['clock_in_time'],
        'clock_out_time': item['clock_out_time'],
        'is_active': item['is_active'],
        'total_seconds': item['total_seconds'],
        'exit_note': item['exit_note'],
        'incident_type': item['incident_type'],
      });
    }).toList();
  }
}
