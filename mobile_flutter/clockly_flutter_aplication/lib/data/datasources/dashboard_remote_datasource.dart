import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';
import '../models/dashboard/dashboard_model.dart';

class DashboardRemoteDatasource {
  const DashboardRemoteDatasource(this._client);

  final ApiClient _client;

  Future<DashboardMetricsModel> getMetrics({String? businessId}) async {
    final params = <String, String>{
      if (businessId != null) 'business_id': businessId,
    };
    final data = await _client.get(ApiConstants.dashboardMetrics, queryParams: params)
        as Map<String, dynamic>;
    return DashboardMetricsModel.fromJson(data);
  }
}
