import 'package:equatable/equatable.dart';

enum AttendanceStatus { active, closed, manualClose }

enum AttendanceMethod { web, mobile, kiosk, rfid, admin, api, unknown }

class AttendanceSessionEntity extends Equatable {
  const AttendanceSessionEntity({
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
  final AttendanceStatus status;
  final AttendanceMethod method;
  final double? locationLat;
  final double? locationLng;
  final double? locationAccuracy;
  final String? notes;
  final String? incidentType;
  final int? closedByAdminId;
  final String? closedByAdminReason;

  bool get isActive => status == AttendanceStatus.active;

  int get effectiveDuration {
    if (durationSeconds != null) return durationSeconds!;
    final end = clockOut ?? DateTime.now();
    return end.difference(clockIn).inSeconds - breakSeconds;
  }

  @override
  List<Object?> get props => [id, businessId, userId, clockIn, clockOut, status];
}

class AttendanceStatusEntity extends Equatable {
  const AttendanceStatusEntity({
    required this.employeeId,
    required this.employeeName,
    required this.isClockedIn,
    this.activeSession,
    this.latestSession,
  });

  final int employeeId;
  final String employeeName;
  final bool isClockedIn;
  final AttendanceSessionEntity? activeSession;
  final AttendanceSessionEntity? latestSession;

  @override
  List<Object?> get props => [employeeId, isClockedIn];
}
