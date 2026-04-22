export type IncidentType =
  | "late_arrival"
  | "early_departure"
  | "absence"
  | "overtime"
  | null;

export interface AttendanceSession {
  id: string;
  company_id: string;
  employee_id: string;
  user_id: string | null;
  clock_in: string;
  clock_out: string | null;
  duration_seconds: number | null;
  status: "open" | "closed" | "voided";
  method: "web" | "kiosk" | "mobile" | "admin";
  notes: string | null;
  created_at: string;
  updated_at: string;
  employee_name?: string;
  employee_initials?: string;
  dni?: string | null;
  closed_by_admin?: boolean;
  incident_label?: string | null;
  severity?: "ok" | "warning" | "critical";
  exit_note?: string | null;
  incident_type?: IncidentType;
  /** UI aliases kept for migrated legacy components. */
  clock_in_time: string;
  clock_out_time: string | null;
  is_active: boolean;
  total_seconds: number | null;
}

export interface SessionReport extends AttendanceSession {
  employee?: {
    id: string;
    full_name: string;
    initials: string;
  };
  total_hours?: number;
}

export interface AttendanceStatus {
  employee: {
    id: string;
    first_name: string;
    last_name: string;
    full_name: string;
    initials: string;
    role: string;
    role_title: string | null;
  };
  is_clocked_in: boolean;
  active_session: AttendanceSession | null;
  last_session: AttendanceSession | null;
}

export interface ClockRequest {
  employee_id?: string;
  session_id?: string;
  method?: "web" | "kiosk" | "mobile" | "admin";
  notes?: string;
}

export interface AttendanceHistoryFilters {
  date_from?: string;
  date_to?: string;
  employee_id?: string;
  status?: "open" | "closed" | "voided";
  incident_filter?: string;
}
