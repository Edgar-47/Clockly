import 'business.dart';
import 'user.dart';

class AuthSession {
  const AuthSession({
    required this.accessToken,
    required this.user,
    required this.businesses,
    required this.permissions,
    this.activeBusinessId,
    this.activeBusinessRole,
  });

  final String accessToken;
  final ClocklyUser user;
  final List<Business> businesses;
  final List<String> permissions;
  final String? activeBusinessId;
  final String? activeBusinessRole;

  Business? get activeBusiness {
    for (final business in businesses) {
      if (business.id == activeBusinessId) return business;
    }
    return null;
  }

  factory AuthSession.fromJson(Map<String, dynamic> json) {
    final businessesJson = json['businesses'];
    final permissionsJson = json['permissions'];
    return AuthSession(
      accessToken: json['access_token']?.toString() ?? '',
      user: ClocklyUser.fromJson(json['user'] as Map<String, dynamic>),
      businesses: businessesJson is List
          ? businessesJson
              .whereType<Map<String, dynamic>>()
              .map(Business.fromJson)
              .toList()
          : const [],
      permissions: permissionsJson is List
          ? permissionsJson.map((value) => value.toString()).toList()
          : const [],
      activeBusinessId: json['active_business_id']?.toString(),
      activeBusinessRole: json['active_business_role']?.toString(),
    );
  }
}
