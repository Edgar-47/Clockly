import '../../../domain/entities/attendance_entity.dart';

class AttendanceSessionModel {
  const AttendanceSessionModel({
    required this.id,
    required this.businessId,
    required this.userId,
    required this.clockIn,
    this.clockOut,
    this.breakSeconds = 0,
    this.durationSeconds,
    required this.status,
    required this.method,
    this.locationLat,
    this.locationLng,
    this.locationAccuracy,
    this.notes,
    this.incidentType,
    this.closedByAdminId,
    this.closedByAdminReason,
  });

  final int id;
  final String businessId;
  final int userId;
  final DateTime clockIn;
  final DateTime? clockOut;
  final int breakSeconds;
  final int? durationSeconds;
  final String status;
  final String method;
  final double? locationLat;
  final double? locationLng;
  final double? locationAccuracy;
  final String? notes;
  final String? incidentType;
  final int? closedByAdminId;
  final String? closedByAdminReason;

  factory AttendanceSessionModel.fromJson(Map<String, dynamic> json) {
    // Derive status: backend sends is_active (bool) or status (string)
    final String status;
    if (json.containsKey('status') && json['status'] is String) {
      status = json['status'] as String;
    } else {
      final isActive = json['is_active'] as bool?;
      final closedByAdmin = json['closed_by_admin'] as bool? ?? false;
      if (closedByAdmin) {
        status = 'manual_close';
      } else {
        status = (isActive ?? true) ? 'active' : 'closed';
      }
    }
    return AttendanceSessionModel(
      id: json['id'] as int,
      businessId: json['business_id']?.toString() ?? '',
      userId: json['user_id'] as int? ?? 0,
      clockIn: DateTime.parse(
        (json['clock_in'] ?? json['clock_in_time'] ?? json['created_at']) as String,
      ),
      clockOut: json['clock_out'] != null || json['clock_out_time'] != null
          ? DateTime.parse((json['clock_out'] ?? json['clock_out_time']) as String)
          : null,
      breakSeconds: json['break_seconds'] as int? ?? 0,
      durationSeconds:
          json['duration_seconds'] as int? ?? json['total_seconds'] as int?,
      status: status,
      method: (json['method'] ?? 'web') as String,
      locationLat: (json['location_lat'] as num?)?.toDouble(),
      locationLng: (json['location_lng'] as num?)?.toDouble(),
      locationAccuracy: (json['location_accuracy'] as num?)?.toDouble(),
      notes: (json['notes'] ?? json['exit_note']) as String?,
      incidentType: json['incident_type'] as String?,
      closedByAdminId:
          json['closed_by_admin_id'] as int? ?? json['closed_by_user_id'] as int?,
      closedByAdminReason:
          json['closed_by_admin_reason'] as String? ?? json['manual_close_reason'] as String?,
    );
  }

  AttendanceSessionEntity toEntity() => AttendanceSessionEntity(
        id: id,
        businessId: businessId,
        userId: userId,
        clockIn: clockIn,
        clockOut: clockOut,
        breakSeconds: breakSeconds,
        durationSeconds: durationSeconds,
        status: _parseStatus(status),
        method: _parseMethod(method),
        locationLat: locationLat,
        locationLng: locationLng,
        locationAccuracy: locationAccuracy,
        notes: notes,
        incidentType: incidentType,
        closedByAdminId: closedByAdminId,
        closedByAdminReason: closedByAdminReason,
      );

  static AttendanceStatus _parseStatus(String s) => switch (s) {
        'active' => AttendanceStatus.active,
        'manual_close' => AttendanceStatus.manualClose,
        _ => AttendanceStatus.closed,
      };

  static AttendanceMethod _parseMethod(String m) {
    final normalized = m.trim().toLowerCase().replaceAll('-', '_');
    return switch (normalized) {
      'web' => AttendanceMethod.web,
      'mobile' || 'app' => AttendanceMethod.mobile,
      'kiosk' => AttendanceMethod.kiosk,
      'rfid' => AttendanceMethod.rfid,
      'admin' => AttendanceMethod.admin,
      'api' => AttendanceMethod.api,
      _ => AttendanceMethod.unknown,
    };
  }
}

class AttendanceStatusModel {
  const AttendanceStatusModel({
    required this.userId,
    required this.fullName,
    required this.isClockedIn,
    this.activeSession,
    this.latestSession,
  });

  final int userId;
  final String fullName;
  final bool isClockedIn;
  final AttendanceSessionModel? activeSession;
  final AttendanceSessionModel? latestSession;

  factory AttendanceStatusModel.fromJson(Map<String, dynamic> json) {
    final employee = json['employee'] as Map<String, dynamic>? ?? {};
    final activeJson = json['active_session'] as Map<String, dynamic>?;
    final latestJson = json['latest_session'] as Map<String, dynamic>?;
    return AttendanceStatusModel(
      userId: (employee['id'] ?? json['user_id'] ?? 0) as int,
      fullName: (employee['full_name'] ?? employee['name'] ?? '') as String,
      isClockedIn: (json['is_clocked_in'] ?? json['isClockedIn'] ?? false) as bool,
      activeSession: activeJson != null ? AttendanceSessionModel.fromJson(activeJson) : null,
      latestSession: latestJson != null ? AttendanceSessionModel.fromJson(latestJson) : null,
    );
  }
}
