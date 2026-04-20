import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

import '../constants/api_constants.dart';
import '../errors/app_exceptions.dart';

class ApiClient {
  ApiClient({http.Client? httpClient})
      : _httpClient = httpClient ?? http.Client();

  final http.Client _httpClient;
  String? _accessToken;

  void setAccessToken(String? token) => _accessToken = token;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
      };

  Future<dynamic> get(String path, {Map<String, String>? queryParams}) async {
    final uri = _buildUri(path, queryParams);
    return _send(() => _httpClient.get(uri, headers: _headers));
  }

  Future<dynamic> post(String path, {Map<String, dynamic>? body}) async {
    final uri = _buildUri(path, null);
    return _send(
      () => _httpClient.post(uri, headers: _headers, body: jsonEncode(body ?? {})),
    );
  }

  Future<dynamic> patch(String path, {Map<String, dynamic>? body}) async {
    final uri = _buildUri(path, null);
    return _send(
      () => _httpClient.patch(uri, headers: _headers, body: jsonEncode(body ?? {})),
    );
  }

  Future<dynamic> put(String path, {Map<String, dynamic>? body}) async {
    final uri = _buildUri(path, null);
    return _send(
      () => _httpClient.put(uri, headers: _headers, body: jsonEncode(body ?? {})),
    );
  }

  Future<dynamic> delete(String path) async {
    final uri = _buildUri(path, null);
    return _send(() => _httpClient.delete(uri, headers: _headers));
  }

  Uri _buildUri(String path, Map<String, String>? queryParams) {
    final base = Uri.parse('${ApiConstants.baseUrl}$path');
    if (queryParams == null || queryParams.isEmpty) return base;
    return base.replace(queryParameters: {...base.queryParameters, ...queryParams});
  }

  Future<dynamic> _send(Future<http.Response> Function() call) async {
    try {
      final response = await call().timeout(const Duration(seconds: 30));
      return _handleResponse(response);
    } on SocketException {
      throw const NetworkException('Sin conexión a internet.');
    } on HttpException {
      throw const NetworkException('Error de red.');
    } on FormatException {
      throw const ServerException('Respuesta inesperada del servidor.');
    }
  }

  dynamic _handleResponse(http.Response response) {
    final body = response.body.isEmpty ? '{}' : response.body;
    dynamic decoded;
    try {
      decoded = jsonDecode(body);
    } catch (_) {
      decoded = <String, dynamic>{};
    }

    switch (response.statusCode) {
      case >= 200 && < 300:
        return decoded;
      case 400:
        final detail = _extractDetail(decoded);
        final fieldErrors = _extractFieldErrors(decoded);
        throw ValidationException(detail ?? 'Datos incorrectos.', fieldErrors: fieldErrors);
      case 401:
        throw const UnauthorizedException();
      case 403:
        throw const ForbiddenException();
      case 404:
        throw const NotFoundException();
      case >= 500:
        throw const ServerException();
      default:
        throw ServerException('Error desconocido (${response.statusCode}).');
    }
  }

  String? _extractDetail(dynamic decoded) {
    if (decoded is Map) {
      return decoded['detail']?.toString() ??
          decoded['message']?.toString() ??
          decoded['non_field_errors']?.toString();
    }
    return null;
  }

  Map<String, List<String>> _extractFieldErrors(dynamic decoded) {
    if (decoded is! Map<String, dynamic>) return {};
    final result = <String, List<String>>{};
    for (final entry in decoded.entries) {
      if (entry.value is List) {
        result[entry.key] = List<String>.from(entry.value.map((e) => e.toString()));
      }
    }
    return result;
  }

  void dispose() => _httpClient.close();
}
