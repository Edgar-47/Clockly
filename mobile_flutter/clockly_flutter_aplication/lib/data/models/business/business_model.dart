import '../../../domain/entities/business_entity.dart';

class BusinessModel {
  const BusinessModel({
    required this.id,
    required this.name,
    required this.type,
    required this.timezone,
    required this.active,
    this.role,
    this.plan,
    this.logoUrl,
  });

  final String id;
  final String name;
  final String type;
  final String timezone;
  final bool active;
  final String? role;
  final String? plan;
  final String? logoUrl;

  factory BusinessModel.fromJson(Map<String, dynamic> json) => BusinessModel(
        id: json['id']?.toString() ?? '',
        name: (json['name'] ?? '') as String,
        type: (json['type'] ?? 'other') as String,
        timezone: (json['timezone'] ?? 'Europe/Madrid') as String,
        active: json['active'] as bool? ?? true,
        role: json['role'] as String?,
        plan: (json['plan'] ?? json['subscription_plan']) as String?,
        logoUrl: json['logo_url'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'type': type,
        'timezone': timezone,
        'active': active,
        if (role != null) 'role': role,
        if (plan != null) 'plan': plan,
      };

  BusinessEntity toEntity() => BusinessEntity(
        id: id,
        name: name,
        type: type,
        timezone: timezone,
        active: active,
        role: role,
        plan: plan,
        logoUrl: logoUrl,
      );
}
