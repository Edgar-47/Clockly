import 'package:equatable/equatable.dart';

class DashboardMetricsEntity extends Equatable {
  const DashboardMetricsEntity({
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
  final List<EmployeeHoursSummary> employeeHours;

  double get attendanceRate {
    if (totalEmployees == 0) return 0;
    return presentToday / totalEmployees * 100;
  }

  @override
  List<Object?> get props => [
        hoursToday,
        hoursWeek,
        hoursMonth,
        activeSessions,
        totalEmployees,
        presentToday,
        absentsToday,
        pendingTickets,
      ];
}

class EmployeeHoursSummary extends Equatable {
  const EmployeeHoursSummary({
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

  String get initials {
    final parts = fullName.trim().split(' ');
    if (parts.length >= 2) return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    return fullName.isNotEmpty ? fullName[0].toUpperCase() : '?';
  }

  @override
  List<Object?> get props => [userId, hoursThisMonth, isClockedIn];
}
