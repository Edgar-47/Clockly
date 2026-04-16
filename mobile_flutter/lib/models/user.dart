class ClocklyUser {
  const ClocklyUser({
    required this.id,
    required this.fullName,
    required this.dni,
    required this.role,
    required this.globalRole,
  });

  final int id;
  final String fullName;
  final String dni;
  final String role;
  final String globalRole;

  factory ClocklyUser.fromJson(Map<String, dynamic> json) {
    return ClocklyUser(
      id: int.parse(json['id'].toString()),
      fullName: json['full_name']?.toString() ?? '',
      dni: json['dni']?.toString() ?? '',
      role: json['role']?.toString() ?? 'employee',
      globalRole: json['global_role']?.toString() ?? 'employee',
    );
  }
}
