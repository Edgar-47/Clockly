import '../../../domain/entities/employee_entity.dart';

class EmployeeModel {
  const EmployeeModel({
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
  final String role;
  final String businessId;
  final bool isActive;
  final String? email;
  final String? phone;
  final String? avatarUrl;
  final DateTime? hiredAt;
  final double? weeklyHours;

  factory EmployeeModel.fromJson(Map<String, dynamic> json) => EmployeeModel(
        id: json['id'] as int,
        fullName: (json['full_name'] ?? json['name'] ?? '') as String,
        identifier: (json['identifier'] ?? json['dni'] ?? json['username'] ?? '') as String,
        role: (json['role'] ?? 'employee') as String,
        businessId: json['business_id']?.toString() ?? '',
        isActive: json['is_active'] as bool? ?? true,
        email: json['email'] as String?,
        phone: json['phone'] as String?,
        avatarUrl: json['avatar_url'] as String?,
        hiredAt: json['hired_at'] != null ? DateTime.tryParse(json['hired_at'] as String) : null,
        weeklyHours: (json['weekly_hours'] as num?)?.toDouble(),
      );

  EmployeeEntity toEntity() => EmployeeEntity(
        id: id,
        fullName: fullName,
        identifier: identifier,
        role: _parseRole(role),
        businessId: businessId,
        isActive: isActive,
        email: email,
        phone: phone,
        avatarUrl: avatarUrl,
        hiredAt: hiredAt,
        weeklyHours: weeklyHours,
      );

  static EmployeeRole _parseRole(String r) => switch (r) {
        'admin' => EmployeeRole.admin,
        'manager' => EmployeeRole.manager,
        _ => EmployeeRole.employee,
      };
}
