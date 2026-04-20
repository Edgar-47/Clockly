import 'package:equatable/equatable.dart';

enum EmployeeRole { admin, manager, employee }

class EmployeeEntity extends Equatable {
  const EmployeeEntity({
    required this.id,
    required this.fullName,
    required this.identifier,
    required this.role,
    required this.businessId,
    required this.isActive,
    this.email,
    this.phone,
    this.avatarUrl,
    this.hiredAt,
    this.weeklyHours,
  });

  final int id;
  final String fullName;
  final String identifier;
  final EmployeeRole role;
  final String businessId;
  final bool isActive;
  final String? email;
  final String? phone;
  final String? avatarUrl;
  final DateTime? hiredAt;
  final double? weeklyHours;

  String get initials {
    final parts = fullName.trim().split(' ');
    if (parts.length >= 2) return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    return fullName.isNotEmpty ? fullName[0].toUpperCase() : '?';
  }

  String get roleLabel {
    return switch (role) {
      EmployeeRole.admin => 'Administrador',
      EmployeeRole.manager => 'Manager',
      EmployeeRole.employee => 'Empleado',
    };
  }

  @override
  List<Object?> get props => [id, fullName, identifier, role, businessId, isActive];
}
