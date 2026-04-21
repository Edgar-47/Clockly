sealed class AppException implements Exception {
  const AppException(this.message);
  final String message;

  @override
  String toString() => message;
}

class NetworkException extends AppException {
  const NetworkException(super.message);
}

class UnauthorizedException extends AppException {
  const UnauthorizedException([super.message = 'Sesión expirada. Por favor inicia sesión de nuevo.']);
}

class ForbiddenException extends AppException {
  const ForbiddenException([super.message = 'No tienes permisos para realizar esta acción.']);
}

class NotFoundException extends AppException {
  const NotFoundException([super.message = 'Recurso no encontrado.']);
}

class ValidationException extends AppException {
  const ValidationException(super.message, {this.fieldErrors = const {}});
  final Map<String, List<String>> fieldErrors;
}

class ServerException extends AppException {
  const ServerException([super.message = 'Error en el servidor. Intenta más tarde.']);

}

class LocationException extends AppException {
  const LocationException([super.message = 'No se pudo obtener la ubicación.']);
}

class StorageException extends AppException {
  const StorageException([super.message = 'Error al guardar datos localmente.']);
}

class SubscriptionLimitException extends AppException {
  const SubscriptionLimitException(super.message);
}

extension AppExceptionMessage on AppException {
  String get userMessage {
    return switch (this) {
      UnauthorizedException() => 'Tu sesión ha expirado. Por favor inicia sesión.',
      ForbiddenException() => 'No tienes permisos para hacer esto.',
      NotFoundException() => 'No se encontró lo que buscabas.',
      ValidationException(:final message) => message,
      NetworkException() => 'Comprueba tu conexión a internet.',
      SubscriptionLimitException(:final message) => message,
      _ => 'Algo salió mal. Intenta de nuevo.',
    };
  }
}
