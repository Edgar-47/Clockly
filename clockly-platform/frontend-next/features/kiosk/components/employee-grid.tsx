"use client";

import { cn, getInitials } from "@/lib/utils";
import { useKioskStore } from "@/features/kiosk/kiosk.store";
import type { AttendanceStatus } from "@/types/attendance";

interface EmployeeGridProps {
  statuses: AttendanceStatus[];
}

export function EmployeeGrid({ statuses }: EmployeeGridProps) {
  const selectEmployee = useKioskStore((s) => s.selectEmployee);

  return (
    <div className="grid grid-cols-3 gap-4 sm:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
      {statuses.map((status) => {
        const { employee, is_clocked_in } = status;
        return (
          <button
            key={employee.id}
            onClick={() => selectEmployee(status)}
            className={cn(
              "flex flex-col items-center gap-3 rounded-xl border-2 p-5 text-center transition-all duration-150 active:scale-95",
              is_clocked_in
                ? "border-success bg-success-bg hover:border-success/70"
                : "border-border bg-white hover:border-primary hover:shadow-sm",
            )}
          >
            <div
              className={cn(
                "flex h-14 w-14 items-center justify-center rounded-full text-lg font-bold",
                is_clocked_in
                  ? "bg-success/20 text-success"
                  : "bg-primary/10 text-primary",
              )}
            >
              {getInitials(employee.first_name, employee.last_name)}
            </div>
            <div>
              <p className="text-sm font-semibold text-ink leading-tight">
                {employee.first_name}
              </p>
              <p className="text-sm font-semibold text-ink leading-tight">
                {employee.last_name}
              </p>
            </div>
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide",
                is_clocked_in
                  ? "bg-success-bg text-success border border-success-border"
                  : "bg-surface-bg text-ink-muted border border-border",
              )}
            >
              <span
                className={cn(
                  "inline-block h-1.5 w-1.5 rounded-full",
                  is_clocked_in ? "bg-success animate-pulse-dot" : "bg-ink-xmuted",
                )}
              />
              {is_clocked_in ? "Fichado" : "Sin fichar"}
            </span>
          </button>
        );
      })}
    </div>
  );
}
