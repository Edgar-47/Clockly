"use client";

import { Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatTime } from "@/lib/format";
import { getInitials } from "@/lib/utils";
import type { AttendanceStatus } from "@/types/attendance";

interface ActiveEmployeesProps {
  statuses?: AttendanceStatus[];
  loading?: boolean;
}

export function ActiveEmployees({ statuses, loading }: ActiveEmployeesProps) {
  return (
    <div className="rounded-lg border border-border bg-white shadow-xs">
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <h2 className="font-bold text-ink">Trabajando ahora</h2>
        {!loading && (
          <Badge variant="success">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-current animate-pulse-dot" />
            {statuses?.length ?? 0} activos
          </Badge>
        )}
      </div>

      <div className="divide-y divide-border">
        {loading &&
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 px-6 py-3">
              <Skeleton className="h-9 w-9 rounded-full" />
              <div className="flex-1 space-y-1.5">
                <Skeleton className="h-3.5 w-32" />
                <Skeleton className="h-3 w-20" />
              </div>
            </div>
          ))}

        {!loading && (!statuses || statuses.length === 0) && (
          <p className="px-6 py-8 text-center text-sm text-ink-muted">
            Ningún empleado trabajando ahora mismo.
          </p>
        )}

        {!loading &&
          statuses?.map((status) => (
            <div
              key={status.employee.id}
              className="flex items-center gap-3 px-6 py-3"
            >
              <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-success-bg text-success text-xs font-bold">
                {getInitials(
                  status.employee.first_name,
                  status.employee.last_name,
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-ink truncate">
                  {status.employee.full_name}
                </p>
                {status.employee.role_title && (
                  <p className="text-xs text-ink-muted">
                    {status.employee.role_title}
                  </p>
                )}
              </div>
              {status.active_session && (
                <div className="flex items-center gap-1 text-xs text-ink-muted">
                  <Clock className="h-3 w-3" />
                  {formatTime(status.active_session.clock_in_time)}
                </div>
              )}
            </div>
          ))}
      </div>
    </div>
  );
}
