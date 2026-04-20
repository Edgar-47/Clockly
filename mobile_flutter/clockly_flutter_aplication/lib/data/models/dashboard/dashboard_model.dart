import '../../../domain/entities/dashboard_entity.dart';

class DashboardMetricsModel {
  const DashboardMetricsModel({
    required this.hoursToday,
    required this.hoursWeek,
    required this.hoursMonth,
    required this.activeSessions,
    required this.totalEmployees,
    required this.presentToday,
    required this.absentsToday,
    required this.pendingTickets,
    this.employeeHours = const [],
  });

  final double hoursToday;
  final double hoursWeek;
  final double hoursMonth;
  final int activeSessions;
  final int totalEmployees;
  final int presentToday;
  final int absentsToday;
  final int pendingTickets;
  final List<EmployeeHoursSummaryModel> employeeHours;

  factory DashboardMetricsModel.fromJson(Map<String, dynamic> json) {
    final employees = json['employee_hours'] as List<dynamic>? ?? [];
    return DashboardMetricsModel(
      hoursToday: (json['hours_today'] as num?)?.toDouble() ?? 0.0,
      hoursWeek: (json['hours_week'] as num?)?.toDouble() ?? 0.0,
      hoursMonth: (json['hours_month'] as num?)?.toDouble() ?? 0.0,
      activeSessions: json['active_sessions'] as int? ?? 0,
      totalEmployees: json['total_employees'] as int? ?? 0,
      presentToday: json['present_today'] as int? ?? 0,
      absentsToday: json['absents_today'] as int? ?? 0,
      pendingTickets: json['pending_tickets'] as int? ?? 0,
      employeeHours: employees
          .map((e) => EmployeeHoursSummaryModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  DashboardMetricsEntity toEntity() => DashboardMetricsEntity(
        hoursToday: hoursToday,
        hoursWeek: hoursWeek,
        hoursMonth: hoursMonth,
        activeSessions: activeSessions,
        totalEmployees: totalEmployees,
        presentToday: presentToday,
        absentsToday: absentsToday,
        pendingTickets: pendingTickets,
        employeeHours: employeeHours.map((e) => e.toEntity()).toList(),
      );
}

class EmployeeHoursSummaryModel {
  const EmployeeHoursSummaryModel({
    required this.userId,
    required this.fullName,
    required this.hoursThisMonth,
    required this.hoursThisWeek,
    required this.isClockedIn,
  });

  final int userId;
  final String fullName;
  final double hoursThisMonth;
  final double hoursThisWeek;
  final bool isClockedIn;

  factory EmployeeHoursSummaryModel.fromJson(Map<String, dynamic> json) =>
      EmployeeHoursSummaryModel(
        userId: json['user_id'] as int? ?? 0,
        fullName: (json['full_name'] ?? json['name'] ?? '') as String,
        hoursThisMonth: (json['hours_month'] as num?)?.toDouble() ?? 0.0,
        hoursThisWeek: (json['hours_week'] as num?)?.toDouble() ?? 0.0,
        isClockedIn: json['is_clocked_in'] as bool? ?? false,
      );

  EmployeeHoursSummary toEntity() => EmployeeHoursSummary(
        userId: userId,
        fullName: fullName,
        hoursThisMonth: hoursThisMonth,
        hoursThisWeek: hoursThisWeek,
        isClockedIn: isClockedIn,
      );
}
