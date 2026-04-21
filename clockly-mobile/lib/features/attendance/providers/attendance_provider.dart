import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';

import '../../../core/errors/app_exceptions.dart';
import '../../../data/models/attendance/attendance_session_model.dart';
import '../../../domain/entities/attendance_entity.dart';
import '../../../providers/app_providers.dart';
import '../../auth/providers/auth_provider.dart';

class AttendanceState {
  const AttendanceState({
    this.status,
    this.statuses = const [],
    this.history = const [],
    this.loading = false,
    this.actionLoading = false,
    this.error,
    this.lastUpdated,
  });

  final AttendanceStatusModel? status;
  final List<AttendanceStatusModel> statuses;
  final List<AttendanceSessionModel> history;
  final bool loading;
  final bool actionLoading;
  final String? error;
  final DateTime? lastUpdated;

  bool get isClockedIn => status?.isClockedIn ?? false;
  AttendanceSessionEntity? get activeSessionEntity =>
      status?.activeSession?.toEntity();

  AttendanceState copyWith({
    AttendanceStatusModel? status,
    List<AttendanceStatusModel>? statuses,
    List<AttendanceSessionModel>? history,
    bool? loading,
    bool? actionLoading,
    String? error,
    DateTime? lastUpdated,
    bool clearError = false,
  }) =>
      AttendanceState(
        status: status ?? this.status,
        statuses: statuses ?? this.statuses,
        history: history ?? this.history,
        loading: loading ?? this.loading,
        actionLoading: actionLoading ?? this.actionLoading,
        error: clearError ? null : (error ?? this.error),
        lastUpdated: lastUpdated ?? this.lastUpdated,
      );
}

class AttendanceNotifier extends AsyncNotifier<AttendanceState> {
  @override
  Future<AttendanceState> build() async {
    final auth = await ref.watch(authProvider.future);
    if (!auth.isAuthenticated) return const AttendanceState();
    return _loadStatus();
  }

  Future<AttendanceState> _loadStatus() async {
    try {
      final datasource = ref.read(attendanceDatasourceProvider);
      final statuses = await datasource.getStatus();
      final myStatus = _resolveMyStatus(statuses);
      return AttendanceState(
        status: myStatus,
        statuses: statuses,
        lastUpdated: DateTime.now(),
      );
    } catch (e) {
      return AttendanceState(error: _msg(e));
    }
  }

  Future<void> refresh() async {
    state = AsyncValue.data((state.valueOrNull ?? const AttendanceState()).copyWith(loading: true));
    try {
      final datasource = ref.read(attendanceDatasourceProvider);
      final statuses = await datasource.getStatus();
      state = AsyncValue.data(AttendanceState(
        status: _resolveMyStatus(statuses),
        statuses: statuses,
        history: state.valueOrNull?.history ?? [],
        lastUpdated: DateTime.now(),
      ));
    } catch (e) {
      state = AsyncValue.data(
        (state.valueOrNull ?? const AttendanceState()).copyWith(loading: false, error: _msg(e)),
      );
    }
  }

  Future<void> loadHistory({DateTime? from, DateTime? to}) async {
    final current = state.valueOrNull ?? const AttendanceState();
    state = AsyncValue.data(current.copyWith(loading: true, clearError: true));
    try {
      final datasource = ref.read(attendanceDatasourceProvider);
      final auth = ref.read(authProvider).valueOrNull;
      final businessId = auth?.session?.activeBusinessId;

      final sessions = await datasource.getHistory(
        businessId: businessId,
        from: from,
        to: to,
      );
      state = AsyncValue.data(current.copyWith(history: sessions, loading: false));
    } catch (e) {
      state = AsyncValue.data(current.copyWith(loading: false, error: _msg(e)));
    }
  }

  Future<bool> clockIn() async {
    final current = state.valueOrNull ?? const AttendanceState();

    // Double-clock-in guard
    if (current.isClockedIn) {
      state = AsyncValue.data(current.copyWith(error: 'Ya tienes una sesión activa.'));
      return false;
    }

    state = AsyncValue.data(current.copyWith(actionLoading: true, clearError: true));
    try {
      final location = await _getLocation();
      final datasource = ref.read(attendanceDatasourceProvider);
      await datasource.clockIn(
        lat: location?.latitude,
        lng: location?.longitude,
        accuracy: location?.accuracy,
      );
      await refresh();
      return true;
    } catch (e) {
      state = AsyncValue.data(current.copyWith(actionLoading: false, error: _msg(e)));
      return false;
    }
  }

  AttendanceStatusModel? _resolveMyStatus(List<AttendanceStatusModel> statuses) {
    if (statuses.isEmpty) return null;
    final userId = ref.read(authProvider).valueOrNull?.session?.userEntity.id;
    if (userId == null) return statuses.first;
    for (final status in statuses) {
      if (status.userId == userId) return status;
    }
    return statuses.first;
  }

  Future<bool> clockOut({String? notes, String? incidentType}) async {
    final current = state.valueOrNull ?? const AttendanceState();

    if (!current.isClockedIn) {
      state = AsyncValue.data(current.copyWith(error: 'No tienes ninguna sesión activa.'));
      return false;
    }

    state = AsyncValue.data(current.copyWith(actionLoading: true, clearError: true));
    try {
      final location = await _getLocation();
      final datasource = ref.read(attendanceDatasourceProvider);
      await datasource.clockOut(
        notes: notes,
        incidentType: incidentType,
        lat: location?.latitude,
        lng: location?.longitude,
        accuracy: location?.accuracy,
      );
      await refresh();
      return true;
    } catch (e) {
      state = AsyncValue.data(current.copyWith(actionLoading: false, error: _msg(e)));
      return false;
    }
  }

  Future<Position?> _getLocation() async {
    try {
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        return null; // Non-blocking: continue without location
      }
      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
      ).timeout(const Duration(seconds: 8));
    } catch (_) {
      return null;
    }
  }

  String _msg(Object e) {
    if (e is AppException) return e.userMessage;
    return 'Error inesperado.';
  }
}

final attendanceProvider = AsyncNotifierProvider<AttendanceNotifier, AttendanceState>(
  AttendanceNotifier.new,
);
