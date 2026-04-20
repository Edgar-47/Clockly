import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../constants/app_constants.dart';
import '../errors/app_exceptions.dart';

class SecureStorage {
  const SecureStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage(
          aOptions: AndroidOptions(encryptedSharedPreferences: true),
        );

  final FlutterSecureStorage _storage;

  Future<void> saveToken(String token) async {
    try {
      await _storage.write(key: AppConstants.tokenKey, value: token);
    } catch (e) {
      throw const StorageException('No se pudo guardar el token.');
    }
  }

  Future<String?> readToken() async {
    try {
      return await _storage.read(key: AppConstants.tokenKey);
    } catch (e) {
      return null;
    }
  }

  Future<void> saveActiveBusinessId(String? id) async {
    try {
      if (id == null) {
        await _storage.delete(key: AppConstants.businessIdKey);
      } else {
        await _storage.write(key: AppConstants.businessIdKey, value: id);
      }
    } catch (_) {}
  }

  Future<String?> readActiveBusinessId() async {
    try {
      return await _storage.read(key: AppConstants.businessIdKey);
    } catch (e) {
      return null;
    }
  }

  Future<void> clear() async {
    try {
      await _storage.deleteAll();
    } catch (_) {}
  }
}
