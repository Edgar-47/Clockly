import 'package:equatable/equatable.dart';

class BusinessEntity extends Equatable {
  const BusinessEntity({
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
  final String? role; // User's role in this business
  final String? plan; // Subscription plan
  final String? logoUrl;

  bool get isAdmin => role == 'admin' || role == 'manager';
  bool get canManageEmployees => role == 'admin' || role == 'manager';
  bool get isProOrEnterprise => plan == 'pro' || plan == 'enterprise';

  @override
  List<Object?> get props => [id, name, type, timezone, active, role, plan];
}
