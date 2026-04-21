import '../../domain/entities/attendance_entity.dart';

extension AttendanceMethodExtension on AttendanceMethod {
  String get label => switch (this) {
        AttendanceMethod.web => 'Web',
        AttendanceMethod.mobile => 'Mobile',
        AttendanceMethod.kiosk => 'Kiosk',
        AttendanceMethod.rfid => 'RFID',
        AttendanceMethod.admin => 'Admin',
        AttendanceMethod.api => 'API',
        AttendanceMethod.unknown => 'Unknown',
      };
}
