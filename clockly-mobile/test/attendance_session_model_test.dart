import 'package:clockly_mobile/data/models/attendance/attendance_session_model.dart';
import 'package:clockly_mobile/domain/entities/attendance_entity.dart';
import 'package:clockly_mobile/shared/extensions/attendance_method_extension.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  Map<String, dynamic> sessionJson({String? method}) => {
        'id': 1,
        'business_id': 'business-1',
        'user_id': 7,
        'clock_in': '2026-04-20T08:00:00Z',
        if (method != null) 'method': method,
      };

  group('AttendanceSessionModel method parsing', () {
    test('supports SaaS attendance methods without relying on enum.name', () {
      final cases = <String, AttendanceMethod>{
        'web': AttendanceMethod.web,
        'mobile': AttendanceMethod.mobile,
        'app': AttendanceMethod.mobile,
        'kiosk': AttendanceMethod.kiosk,
        'rfid': AttendanceMethod.rfid,
        'admin': AttendanceMethod.admin,
        'api': AttendanceMethod.api,
      };

      for (final entry in cases.entries) {
        final entity =
            AttendanceSessionModel.fromJson(sessionJson(method: entry.key))
                .toEntity();

        expect(entity.method, entry.value);
      }
    });

    test('uses a stable UI label instead of enum.name', () {
      final entity =
          AttendanceSessionModel.fromJson(sessionJson(method: 'rfid')).toEntity();

      expect(entity.method.label, 'RFID');
    });

    test('falls back safely for missing or unknown method values', () {
      expect(
        AttendanceSessionModel.fromJson(sessionJson()).toEntity().method,
        AttendanceMethod.web,
      );
      expect(
        AttendanceSessionModel.fromJson(sessionJson(method: 'future_terminal'))
            .toEntity()
            .method,
        AttendanceMethod.unknown,
      );
      expect(AttendanceMethod.unknown.label, 'Unknown');
    });
  });
}
