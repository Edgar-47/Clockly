import { api } from "@/lib/api-client";
import type { DashboardSummary, MetricsOverview } from "@/types/dashboard";
import { attendanceService } from "./attendance.service";
import { employeesService } from "./employees.service";

export const dashboardService = {
  summary: async (): Promise<DashboardSummary> => {
    const [metrics, employees, statuses, sessions] = await Promise.all([
      api.get<MetricsOverview>("/metrics/overview"),
      employeesService.list(),
      attendanceService.current(),
      attendanceService.history(),
    ]);

    const clockedIn = statuses.filter((s) => s.is_clocked_in);
    const recentSessions = sessions
      .filter((session) => !session.is_active)
      .slice(0, 8);

    return {
      business: null,
      usage: null,
      total_employees: employees.filter((employee) => employee.is_active).length,
      total_clocked_in: clockedIn.length,
      total_clocked_out: Math.max(0, employees.filter((employee) => employee.is_active).length - clockedIn.length),
      clocked_in_statuses: clockedIn,
      recent_sessions: recentSessions,
      kpis: {
        total_hours_today: metrics.worked_seconds,
        total_hours_week: metrics.worked_seconds,
        total_hours_month: metrics.worked_seconds,
        month_overtime_seconds: 0,
        avg_hours_per_day: metrics.worked_seconds,
        attendance_rate: employees.length ? clockedIn.length / employees.length : 0,
        total_incidents: 0,
        top_worker_this_week: metrics.employees[0]?.employee_name ?? null,
        busiest_hour_today: null,
        busiest_concurrent_today: metrics.open_sessions,
      },
    };
  },
};
