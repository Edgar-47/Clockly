import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exceptions.dart';
import '../../../data/models/dashboard/dashboard_model.dart';
import '../../../providers/app_providers.dart';
import '../../auth/providers/auth_provider.dart';

class DashboardNotifier extends AsyncNotifier<DashboardMetricsModel?> {
  @override
  Future<DashboardMetricsModel?> build() async {
    final auth = await ref.watch(authProvider.future);
    if (!auth.isAuthenticated) return null;
    return _load();
  }

  Future<DashboardMetricsModel?> _load() async {
    final auth = ref.read(authProvider).valueOrNull;
    final businessId = auth?.session?.activeBusinessId;
    final datasource = ref.read(dashboardDatasourceProvider);
    return datasource.getMetrics(businessId: businessId);
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_load);
  }
}

final dashboardProvider = AsyncNotifierProvider<DashboardNotifier, DashboardMetricsModel?>(
  DashboardNotifier.new,
);
