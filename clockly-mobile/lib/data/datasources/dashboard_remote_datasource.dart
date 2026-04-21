import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';
import '../models/dashboard/dashboard_model.dart';

class DashboardRemoteDatasource {
  const DashboardRemoteDatasource(this._client);

  final ApiClient _client;

  Future<DashboardMetricsModel> getMetrics({String? businessId}) async {
    // business_id is derived from the JWT token on the backend; no query param needed
    final data = await _client.get(ApiConstants.dashboardMetrics)
        as Map<String, dynamic>;
    return DashboardMetricsModel.fromJson(data);
  }
}
