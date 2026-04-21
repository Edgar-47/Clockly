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
    // Backend response shape from GET /dashboard/summary:
    // { total_employees, total_clocked_in, total_clocked_out,
    //   kpis: { total_hours_today, total_hours_week, total_hours_month, ... } }
    final kpis = json['kpis'] as Map<String, dynamic>?;
    final totalClockedIn = json['total_clocked_in'] as int? ?? 0;
    final totalClockedOut = json['total_clocked_out'] as int? ?? 0;

    return DashboardMetricsModel(
      hoursToday: (kpis?['total_hours_today'] as num?)?.toDouble() ?? 0.0,
      hoursWeek: (kpis?['total_hours_week'] as num?)?.toDouble() ?? 0.0,
      hoursMonth: (kpis?['total_hours_month'] as num?)?.toDouble() ?? 0.0,
      activeSessions: totalClockedIn,
      totalEmployees: json['total_employees'] as int? ?? 0,
      presentToday: totalClockedIn,
      absentsToday: totalClockedOut,
      pendingTickets: json['pending_tickets'] as int? ?? 0,
      employeeHours: const [],
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
