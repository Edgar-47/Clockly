import '../../../domain/entities/user_entity.dart';

class UserModel {
  const UserModel({
    required this.id,
    required this.fullName,
    required this.identifier,
    required this.globalRole,
    this.email,
    this.avatarUrl,
  });

  final int id;
  final String fullName;
  final String identifier;
  final String globalRole;
  final String? email;
  final String? avatarUrl;

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
        id: json['id'] as int,
        fullName: (json['full_name'] ?? json['fullName'] ?? json['name'] ?? '') as String,
        identifier: (json['identifier'] ?? json['dni'] ?? json['username'] ?? '') as String,
        globalRole: (json['global_role'] ?? json['role'] ?? 'employee') as String,
        email: json['email'] as String?,
        avatarUrl: json['avatar_url'] as String?,
      );

  UserEntity toEntity() => UserEntity(
        id: id,
        fullName: fullName,
        identifier: identifier,
        globalRole: globalRole,
        email: email,
        avatarUrl: avatarUrl,
      );
}
