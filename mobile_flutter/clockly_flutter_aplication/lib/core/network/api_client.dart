import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

import '../constants/api_constants.dart';
import '../errors/app_exceptions.dart';

class ApiClient {
  ApiClient({http.Client? httpClient, int maxRetries = 1})
      : _httpClient = httpClient ?? http.Client(),
        _maxRetries = maxRetries;

  final http.Client _httpClient;
  final int _maxRetries;
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

  // POST/PATCH/PUT/DELETE are not retried to prevent duplicate mutations.
  Future<dynamic> post(String path, {Map<String, dynamic>? body}) async {
    final uri = _buildUri(path, null);
    return _send(
      () => _httpClient.post(uri, headers: _headers, body: jsonEncode(body ?? {})),
      retryable: false,
    );
  }

  Future<dynamic> patch(String path, {Map<String, dynamic>? body}) async {
    final uri = _buildUri(path, null);
    return _send(
      () => _httpClient.patch(uri, headers: _headers, body: jsonEncode(body ?? {})),
      retryable: false,
    );
  }

  Future<dynamic> put(String path, {Map<String, dynamic>? body}) async {
    final uri = _buildUri(path, null);
    return _send(
      () => _httpClient.put(uri, headers: _headers, body: jsonEncode(body ?? {})),
      retryable: false,
    );
  }

  Future<dynamic> delete(String path) async {
    final uri = _buildUri(path, null);
    return _send(
      () => _httpClient.delete(uri, headers: _headers),
      retryable: false,
    );
  }

  Uri _buildUri(String path, Map<String, String>? queryParams) {
    final base = Uri.parse('${ApiConstants.baseUrl}$path');
    if (queryParams == null || queryParams.isEmpty) return base;
    return base.replace(queryParameters: {...base.queryParameters, ...queryParams});
  }

  Future<dynamic> _send(
    Future<http.Response> Function() call, {
    bool retryable = true,
  }) async {
    int attempts = 0;
    while (true) {
      attempts++;
      try {
        final response = await call().timeout(const Duration(seconds: 30));
        // Retry on 5xx only for safe, idempotent-ish transient errors.
        if (retryable && response.statusCode >= 500 && attempts <= _maxRetries) {
          await Future.delayed(Duration(milliseconds: 500 * attempts));
          continue;
        }
        return _handleResponse(response);
      } on SocketException {
        if (retryable && attempts <= _maxRetries) {
          await Future.delayed(Duration(milliseconds: 500 * attempts));
          continue;
        }
        throw const NetworkException('Sin conexión a internet.');
      } on HttpException {
        throw const NetworkException('Error de red.');
      } on TimeoutException {
        if (retryable && attempts <= _maxRetries) {
          continue;
        }
        throw const NetworkException('El servidor tardó demasiado en responder.');
      } on FormatException {
        throw const ServerException('Respuesta inesperada del servidor.');
      }
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
        throw ForbiddenException(_extractDetail(decoded) ?? 'No tienes permisos para realizar esta acción.');
      case 404:
        throw NotFoundException(_extractDetail(decoded) ?? 'Recurso no encontrado.');
      case >= 500:
        throw const ServerException();
      default:
        throw ServerException('Error desconocido (${response.statusCode}).');
    }
  }

  String? _extractDetail(dynamic decoded) {
    if (decoded is Map) {
      // Backend format: {"error": {"code": "...", "message": "..."}}
      final error = decoded['error'];
      if (error is Map) return error['message']?.toString();
      // Fallback for other formats
      return decoded['detail']?.toString() ??
          decoded['message']?.toString() ??
          decoded['non_field_errors']?.toString();
    }
    return null;
  }

  Map<String, List<String>> _extractFieldErrors(dynamic decoded) {
    if (decoded is! Map<String, dynamic>) return {};
    final result = <String, List<String>>{};
    final error = decoded['error'];
    final details = error is Map ? error['details'] : null;
    final backendErrors = details is Map ? details['errors'] : null;
    if (backendErrors is List) {
      for (final item in backendErrors) {
        if (item is Map) {
          final loc = item['loc'];
          final field = loc is List && loc.isNotEmpty ? loc.last.toString() : 'form';
          final message = item['msg']?.toString() ?? 'Dato no válido.';
          result.putIfAbsent(field, () => []).add(message);
        }
      }
    }
    for (final entry in decoded.entries) {
      if (entry.value is List) {
        result[entry.key] = List<String>.from(entry.value.map((e) => e.toString()));
      }
    }
    return result;
  }

  void dispose() => _httpClient.close();
}
