import type { AttendanceStatus, SessionReport } from "./attendance";

export interface DashboardKPIs {
  total_hours_today: number;
  total_hours_week: number;
  total_hours_month: number;
  month_overtime_seconds: number;
  avg_hours_per_day: number;
  attendance_rate: number;
  total_incidents: number;
  top_worker_this_week?: string | null;
  busiest_hour_today?: number | null;
  busiest_concurrent_today?: number;
}

export interface PlanUsage {
  plan: {
    code: string;
    name: string;
    max_employees: number;
    max_admins: number;
  };
  employee_count: number;
  admin_count: number;
}

export interface DashboardSummary {
  business: {
    id: string;
    name: string;
    role: string;
  } | null;
  usage: PlanUsage | null;
  total_employees: number;
  total_clocked_in: number;
  total_clocked_out: number;
  clocked_in_statuses: AttendanceStatus[];
  recent_sessions: SessionReport[];
  kpis: DashboardKPIs | null;
}

export interface MetricsOverview {
  worked_seconds: number;
  open_sessions: number;
  active_employees: number;
  employees: Array<{
    employee_id: string;
    employee_name: string;
    worked_seconds: number;
    closed_sessions: number;
  }>;
}
