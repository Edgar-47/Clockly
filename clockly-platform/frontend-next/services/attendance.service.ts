import { api } from "@/lib/api-client";
import type {
  AttendanceStatus,
  ClockRequest,
  AttendanceSession,
  SessionReport,
  AttendanceHistoryFilters,
} from "@/types/attendance";
import { employeesService } from "./employees.service";

function normalizeSession(session: AttendanceSession): AttendanceSession {
  return {
    ...session,
    clock_in_time: session.clock_in_time ?? session.clock_in,
    clock_out_time: session.clock_out_time ?? session.clock_out,
    is_active: session.is_active ?? session.status === "open",
    total_seconds: session.total_seconds ?? session.duration_seconds,
  };
}

export const attendanceService = {
  current: async () => {
    const [employees, sessions] = await Promise.all([
      employeesService.list(),
      attendanceService.history({ status: "open" }),
    ]);
    return employees
      .filter((employee) => employee.is_active)
      .map((employee): AttendanceStatus => {
        const active = sessions.find((s) => s.employee_id === employee.id) ?? null;
        return {
          employee: {
            id: employee.id,
            first_name: employee.first_name,
            last_name: employee.last_name,
            full_name: employee.full_name,
            initials: employee.initials,
            role: "employee",
            role_title: employee.role_title,
          },
          is_clocked_in: Boolean(active),
          active_session: active,
          last_session: null,
        };
      });
  },

  clockIn: (payload?: ClockRequest) =>
    api.post<AttendanceSession>("/attendance/clock-in", payload).then(normalizeSession),

  clockOut: (payload?: ClockRequest) =>
    api.post<AttendanceSession>("/attendance/clock-out", payload).then(normalizeSession),

  history: (filters: AttendanceHistoryFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.date_from) params.set("date_from", filters.date_from);
    if (filters.date_to) params.set("date_to", filters.date_to);
    if (filters.employee_id)
      params.set("employee_id", String(filters.employee_id));
    if (filters.status) params.set("status", filters.status);
    const qs = params.toString();
    return api
      .get<{ items: SessionReport[] }>(
        `/attendance/sessions${qs ? `?${qs}` : ""}`,
      )
      .then((r) => r.items.map(normalizeSession));
  },

  exportUrl: (format: "excel" | "pdf", filters: AttendanceHistoryFilters = {}) => {
    const params = new URLSearchParams({ format });
    if (filters.date_from) params.set("date_from", filters.date_from);
    if (filters.date_to) params.set("date_to", filters.date_to);
    if (filters.employee_id) params.set("employee_id", filters.employee_id);
    if (filters.status) params.set("status", filters.status);
    return `${process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8010"}/exports/attendance?${params}`;
  },
};
