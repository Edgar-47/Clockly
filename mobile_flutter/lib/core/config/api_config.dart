class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'CLOCKLY_API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000/api/v1',
  );
}
