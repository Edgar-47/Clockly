import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/network/api_client.dart';
import '../core/storage/secure_storage.dart';
import '../data/datasources/auth_remote_datasource.dart';
import '../data/datasources/attendance_remote_datasource.dart';
import '../data/datasources/employee_remote_datasource.dart';
import '../data/datasources/ticket_remote_datasource.dart';
import '../data/datasources/dashboard_remote_datasource.dart';

// Singletons — never dispose these
final apiClientProvider = Provider<ApiClient>((ref) {
  final client = ApiClient();
  ref.onDispose(client.dispose);
  return client;
});

final secureStorageProvider = Provider<SecureStorage>((ref) {
  return const SecureStorage();
});

// Datasources
final authDatasourceProvider = Provider<AuthRemoteDatasource>((ref) {
  return AuthRemoteDatasource(ref.watch(apiClientProvider));
});

final attendanceDatasourceProvider = Provider<AttendanceRemoteDatasource>((ref) {
  return AttendanceRemoteDatasource(ref.watch(apiClientProvider));
});

final employeeDatasourceProvider = Provider<EmployeeRemoteDatasource>((ref) {
  return EmployeeRemoteDatasource(ref.watch(apiClientProvider));
});

final ticketDatasourceProvider = Provider<TicketRemoteDatasource>((ref) {
  return TicketRemoteDatasource(ref.watch(apiClientProvider));
});

final dashboardDatasourceProvider = Provider<DashboardRemoteDatasource>((ref) {
  return DashboardRemoteDatasource(ref.watch(apiClientProvider));
});
