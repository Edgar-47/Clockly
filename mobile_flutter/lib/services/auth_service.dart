import '../core/network/api_client.dart';
import '../models/auth_session.dart';

class AuthService {
  const AuthService(this._apiClient);

  final ApiClient _apiClient;

  Future<AuthSession> login({
    required String identifier,
    required String password,
  }) async {
    final json = await _apiClient.post('/auth/login', body: {
      'identifier': identifier,
      'password': password,
    });
    final session = AuthSession.fromJson(json);
    _apiClient.setAccessToken(session.accessToken);
    return session;
  }

  Future<AuthSession> me() async {
    final json = await _apiClient.get('/auth/me');
    final session = AuthSession.fromJson(json);
    _apiClient.setAccessToken(session.accessToken);
    return session;
  }

  Future<void> logout() async {
    await _apiClient.post('/auth/logout');
    _apiClient.setAccessToken(null);
  }
}
