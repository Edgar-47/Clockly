import 'user.dart';

class AttendanceSession {
  const AttendanceSession({
    required this.id,
    required this.userId,
    required this.clockInTime,
    required this.isActive,
    this.businessId,
    this.clockOutTime,
    this.totalSeconds,
    this.exitNote,
    this.incidentType,
  });

  final int id;
  final int userId;
  final String? businessId;
  final DateTime clockInTime;
  final DateTime? clockOutTime;
  final bool isActive;
  final int? totalSeconds;
  final String? exitNote;
  final String? incidentType;

  factory AttendanceSession.fromJson(Map<String, dynamic> json) {
    return AttendanceSession(
      id: int.parse(json['id'].toString()),
      userId: int.parse(json['user_id'].toString()),
      businessId: json['business_id']?.toString(),
      clockInTime: DateTime.parse(json['clock_in_time'].toString()),
      clockOutTime: json['clock_out_time'] == null
          ? null
          : DateTime.parse(json['clock_out_time'].toString()),
      isActive: json['is_active'] == true,
      totalSeconds: json['total_seconds'] == null
          ? null
          : int.parse(json['total_seconds'].toString()),
      exitNote: json['exit_note']?.toString(),
      incidentType: json['incident_type']?.toString(),
    );
  }
}

class AttendanceStatus {
  const AttendanceStatus({
    required this.employee,
    required this.isClockedIn,
    this.activeSession,
    this.latestSession,
  });

  final ClocklyUser employee;
  final bool isClockedIn;
  final AttendanceSession? activeSession;
  final AttendanceSession? latestSession;

  factory AttendanceStatus.fromJson(Map<String, dynamic> json) {
    return AttendanceStatus(
      employee: ClocklyUser.fromJson(json['employee'] as Map<String, dynamic>),
      isClockedIn: json['is_clocked_in'] == true,
      activeSession: json['active_session'] is Map<String, dynamic>
          ? AttendanceSession.fromJson(json['active_session'] as Map<String, dynamic>)
          : null,
      latestSession: json['latest_session'] is Map<String, dynamic>
          ? AttendanceSession.fromJson(json['latest_session'] as Map<String, dynamic>)
          : null,
    );
  }
}
