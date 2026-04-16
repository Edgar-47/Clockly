class Business {
  const Business({
    required this.id,
    required this.name,
    required this.type,
    required this.timezone,
    required this.active,
    this.role,
  });

  final String id;
  final String name;
  final String type;
  final String timezone;
  final bool active;
  final String? role;

  factory Business.fromJson(Map<String, dynamic> json) {
    return Business(
      id: json['id'].toString(),
      name: json['business_name']?.toString() ?? '',
      type: json['business_type']?.toString() ?? 'otro',
      timezone: json['timezone']?.toString() ?? 'Europe/Madrid',
      active: json['active'] == true,
      role: json['role']?.toString(),
    );
  }
}
