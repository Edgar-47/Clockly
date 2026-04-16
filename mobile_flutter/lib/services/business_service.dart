import '../core/network/api_client.dart';
import '../models/auth_session.dart';
import '../models/business.dart';

class BusinessService {
  const BusinessService(this._apiClient);

  final ApiClient _apiClient;

  Future<List<Business>> listBusinesses() async {
    final json = await _apiClient.get('/businesses');
    final items = json['items'];
    if (items is! List) return const [];
    return items
        .whereType<Map<String, dynamic>>()
        .map(Business.fromJson)
        .toList();
  }

  Future<AuthSession> switchBusiness(String businessId) async {
    final json = await _apiClient.post('/businesses/switch', body: {
      'business_id': businessId,
    });
    final authJson = json['auth'] as Map<String, dynamic>;
    final session = AuthSession.fromJson(authJson);
    _apiClient.setAccessToken(session.accessToken);
    return session;
  }
}
