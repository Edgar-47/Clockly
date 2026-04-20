import 'package:equatable/equatable.dart';

class UserEntity extends Equatable {
  const UserEntity({
    required this.id,
    required this.fullName,
    required this.identifier,
    required this.globalRole,
    this.email,
    this.avatarUrl,
  });

  final int id;
  final String fullName;
  final String identifier; // DNI / email / username
  final String globalRole;
  final String? email;
  final String? avatarUrl;

  String get initials {
    final parts = fullName.trim().split(' ');
    if (parts.length >= 2) return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    return fullName.isNotEmpty ? fullName[0].toUpperCase() : '?';
  }

  bool get isSuperadmin => globalRole == 'superadmin';

  @override
  List<Object?> get props => [id, fullName, identifier, globalRole, email];
}
