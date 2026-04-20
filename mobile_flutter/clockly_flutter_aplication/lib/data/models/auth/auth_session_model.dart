import '../../../domain/entities/user_entity.dart';
import '../../../domain/entities/business_entity.dart';
import '../business/business_model.dart';
import 'user_model.dart';

class AuthSessionModel {
  const AuthSessionModel({
    required this.accessToken,
    required this.user,
    required this.businesses,
    required this.permissions,
    this.activeBusinessId,
    this.activeBusinessRole,
  });

  final String accessToken;
  final UserModel user;
  final List<BusinessModel> businesses;
  final List<String> permissions;
  final String? activeBusinessId;
  final String? activeBusinessRole;

  factory AuthSessionModel.fromJson(Map<String, dynamic> json) {
    final businessesJson = json['businesses'] as List<dynamic>? ?? [];
    return AuthSessionModel(
      accessToken: (json['access'] ?? json['access_token'] ?? json['token'] ?? '') as String,
      user: UserModel.fromJson(
        json['user'] as Map<String, dynamic>? ?? {},
      ),
      businesses: businessesJson
          .map((b) => BusinessModel.fromJson(b as Map<String, dynamic>))
          .toList(),
      permissions: List<String>.from(json['permissions'] as List<dynamic>? ?? []),
      activeBusinessId: json['active_business_id'] as String?,
      activeBusinessRole: json['active_business_role'] as String?,
    );
  }

  UserEntity get userEntity => user.toEntity();

  List<BusinessEntity> get businessEntities =>
      businesses.map((b) => b.toEntity()).toList();

  BusinessEntity? get activeBusiness => businessEntities.cast<BusinessEntity?>().firstWhere(
        (b) => b?.id == activeBusinessId,
        orElse: () => businessEntities.isNotEmpty ? businessEntities.first : null,
      );

  bool hasPermission(String permission) => permissions.contains(permission);
}
