import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';
import '../models/auth/auth_session_model.dart';

class AuthRemoteDatasource {
  const AuthRemoteDatasource(this._client);

  final ApiClient _client;

  Future<AuthSessionModel> login({
    required String identifier,
    required String password,
  }) async {
    final data = await _client.post(
      ApiConstants.login,
      body: {'identifier': identifier, 'password': password},
    ) as Map<String, dynamic>;
    final session = AuthSessionModel.fromJson(data);
    _client.setAccessToken(session.accessToken);
    return session;
  }

  Future<AuthSessionModel> me() async {
    final data = await _client.get(ApiConstants.me) as Map<String, dynamic>;
    return AuthSessionModel.fromJson(data);
  }

  Future<AuthSessionModel> switchBusiness(String businessId) async {
    final data = await _client.post(
      ApiConstants.switchBusiness,
      body: {'business_id': businessId},
    ) as Map<String, dynamic>;
    // Backend returns {"business": {...}, "auth": {...}} — auth payload is nested
    final authPayload = data['auth'] as Map<String, dynamic>? ?? data;
    final session = AuthSessionModel.fromJson(authPayload);
    _client.setAccessToken(session.accessToken);
    return session;
  }

  Future<void> logout() async {
    try {
      await _client.post(ApiConstants.logout);
    } catch (_) {
      // Always succeed locally even if server call fails
    } finally {
      _client.setAccessToken(null);
    }
  }
}
