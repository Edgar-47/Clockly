import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exceptions.dart';
import '../../../data/models/employee/employee_model.dart';
import '../../../providers/app_providers.dart';
import '../../auth/providers/auth_provider.dart';

class EmployeesState {
  const EmployeesState({
    this.employees = const [],
    this.loading = false,
    this.error,
    this.searchQuery = '',
  });

  final List<EmployeeModel> employees;
  final bool loading;
  final String? error;
  final String searchQuery;

  List<EmployeeModel> get filtered {
    if (searchQuery.isEmpty) return employees;
    final q = searchQuery.toLowerCase();
    return employees.where((e) {
      return e.fullName.toLowerCase().contains(q) ||
          e.identifier.toLowerCase().contains(q) ||
          (e.email?.toLowerCase().contains(q) ?? false);
    }).toList();
  }

  EmployeesState copyWith({
    List<EmployeeModel>? employees,
    bool? loading,
    String? error,
    String? searchQuery,
    bool clearError = false,
  }) =>
      EmployeesState(
        employees: employees ?? this.employees,
        loading: loading ?? this.loading,
        error: clearError ? null : (error ?? this.error),
        searchQuery: searchQuery ?? this.searchQuery,
      );
}

class EmployeesNotifier extends AsyncNotifier<EmployeesState> {
  @override
  Future<EmployeesState> build() async {
    final auth = await ref.watch(authProvider.future);
    if (!auth.isAuthenticated) return const EmployeesState();
    return _load();
  }

  Future<EmployeesState> _load() async {
    try {
      final auth = ref.read(authProvider).valueOrNull;
      final businessId = auth?.session?.activeBusinessId;
      final datasource = ref.read(employeeDatasourceProvider);
      final employees = await datasource.getEmployees(businessId: businessId);
      return EmployeesState(employees: employees);
    } catch (e) {
      return EmployeesState(error: _msg(e));
    }
  }

  Future<void> refresh() async {
    final current = state.valueOrNull ?? const EmployeesState();
    state = AsyncValue.data(current.copyWith(loading: true, clearError: true));
    final next = await _load();
    state = AsyncValue.data(next.copyWith(searchQuery: current.searchQuery));
  }

  void setSearch(String query) {
    final current = state.valueOrNull;
    if (current == null) return;
    state = AsyncValue.data(current.copyWith(searchQuery: query));
  }

  String _msg(Object e) {
    if (e is AppException) return e.userMessage;
    return 'Error cargando empleados.';
  }
}

final employeesProvider = AsyncNotifierProvider<EmployeesNotifier, EmployeesState>(
  EmployeesNotifier.new,
);
