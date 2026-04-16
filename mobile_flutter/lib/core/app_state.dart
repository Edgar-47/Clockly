import 'package:flutter/foundation.dart';

import '../models/attendance.dart';
import '../models/auth_session.dart';
import '../repositories/clockly_repository.dart';

class AppState extends ChangeNotifier {
  AppState(this._repository);

  final ClocklyRepository _repository;

  AuthSession? session;
  AttendanceStatus? attendanceStatus;
  List<AttendanceSession> history = const [];
  bool loading = false;
  String? error;

  bool get isAuthenticated => session != null;

  Future<void> restore() async {
    await _run(() async {
      session = await _repository.restoreSession();
      if (session != null) await refreshAttendance();
    });
  }

  Future<void> login(String identifier, String password) async {
    await _run(() async {
      session = await _repository.login(identifier, password);
      await refreshAttendance();
    });
  }

  Future<void> switchBusiness(String businessId) async {
    await _run(() async {
      session = await _repository.switchBusiness(businessId);
      await refreshAttendance();
    });
  }

  Future<void> refreshAttendance() async {
    final statuses = await _repository.currentAttendance();
    attendanceStatus = statuses.isEmpty ? null : statuses.first;
    history = await _repository.history();
    notifyListeners();
  }

  Future<void> clockIn() async {
    await _run(() async {
      await _repository.clockIn();
      await refreshAttendance();
    });
  }

  Future<void> clockOut({String? exitNote, String? incidentType}) async {
    await _run(() async {
      await _repository.clockOut(
        exitNote: exitNote,
        incidentType: incidentType,
      );
      await refreshAttendance();
    });
  }

  Future<void> logout() async {
    await _run(() async {
      await _repository.logout();
      session = null;
      attendanceStatus = null;
      history = const [];
    });
  }

  Future<void> _run(Future<void> Function() action) async {
    loading = true;
    error = null;
    notifyListeners();
    try {
      await action();
    } catch (exception) {
      error = exception.toString();
    } finally {
      loading = false;
      notifyListeners();
    }
  }
}
