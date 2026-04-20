import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exceptions.dart';
import '../../../data/models/auth/auth_session_model.dart';
import '../../../providers/app_providers.dart';

class AuthState {
  const AuthState({
    this.session,
    this.loading = false,
    this.error,
    this.isInitialized = false,
  });

  final AuthSessionModel? session;
  final bool loading;
  final String? error;
  final bool isInitialized;

  bool get isAuthenticated => session != null;

  AuthState copyWith({
    AuthSessionModel? session,
    bool? loading,
    String? error,
    bool? isInitialized,
    bool clearSession = false,
    bool clearError = false,
  }) =>
      AuthState(
        session: clearSession ? null : (session ?? this.session),
        loading: loading ?? this.loading,
        error: clearError ? null : (error ?? this.error),
        isInitialized: isInitialized ?? this.isInitialized,
      );
}

class AuthNotifier extends AsyncNotifier<AuthState> {
  @override
  Future<AuthState> build() async {
    return _restoreSession();
  }

  Future<AuthState> _restoreSession() async {
    final storage = ref.read(secureStorageProvider);
    final client = ref.read(apiClientProvider);
    final datasource = ref.read(authDatasourceProvider);

    final token = await storage.readToken();
    if (token == null) {
      return const AuthState(isInitialized: true);
    }

    client.setAccessToken(token);
    try {
      final session = await datasource.me();
      return AuthState(session: session, isInitialized: true);
    } on UnauthorizedException {
      await storage.clear();
      client.setAccessToken(null);
      return const AuthState(isInitialized: true);
    } catch (_) {
      // Network error but token might be valid — keep session for offline
      return const AuthState(isInitialized: true);
    }
  }

  Future<void> login({required String identifier, required String password}) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final datasource = ref.read(authDatasourceProvider);
      final storage = ref.read(secureStorageProvider);

      final session = await datasource.login(
        identifier: identifier,
        password: password,
      );
      await storage.saveToken(session.accessToken);
      if (session.activeBusinessId != null) {
        await storage.saveActiveBusinessId(session.activeBusinessId);
      }
      return AuthState(session: session, isInitialized: true);
    });
  }

  Future<void> switchBusiness(String businessId) async {
    final current = state.valueOrNull;
    if (current?.session == null) return;

    state = AsyncValue.data(current!.copyWith(loading: true));
    try {
      final datasource = ref.read(authDatasourceProvider);
      final storage = ref.read(secureStorageProvider);

      final session = await datasource.switchBusiness(businessId);
      await storage.saveToken(session.accessToken);
      await storage.saveActiveBusinessId(businessId);

      state = AsyncValue.data(AuthState(session: session, isInitialized: true));
    } catch (e) {
      state = AsyncValue.data(
        current.copyWith(loading: false, error: _errorMessage(e)),
      );
    }
  }

  Future<void> logout() async {
    try {
      await ref.read(authDatasourceProvider).logout();
    } catch (_) {}
    await ref.read(secureStorageProvider).clear();
    state = const AsyncValue.data(AuthState(isInitialized: true));
  }

  String _errorMessage(Object e) {
    if (e is AppException) return e.userMessage;
    return 'Error inesperado. Intenta de nuevo.';
  }
}

final authProvider = AsyncNotifierProvider<AuthNotifier, AuthState>(
  AuthNotifier.new,
);
