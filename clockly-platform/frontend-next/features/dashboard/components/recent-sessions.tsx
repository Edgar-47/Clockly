"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { formatDateTime, formatSeconds } from "@/lib/format";
import type { SessionReport } from "@/types/attendance";

interface RecentSessionsProps {
  sessions?: SessionReport[];
  loading?: boolean;
}

export function RecentSessions({ sessions, loading }: RecentSessionsProps) {
  return (
    <div className="rounded-lg border border-border bg-white shadow-xs">
      <div className="border-b border-border px-6 py-4">
        <h2 className="font-bold text-ink">Últimos fichajes</h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-muted text-left">
              <th className="px-6 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">
                Empleado
              </th>
              <th className="px-6 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">
                Entrada
              </th>
              <th className="px-6 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">
                Salida
              </th>
              <th className="px-6 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">
                Duración
              </th>
              <th className="px-6 py-3 text-xs font-semibold text-ink-muted uppercase tracking-wide">
                Estado
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {loading &&
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 5 }).map((_, j) => (
                    <td key={j} className="px-6 py-3">
                      <Skeleton className="h-4 w-24" />
                    </td>
                  ))}
                </tr>
              ))}

            {!loading && (!sessions || sessions.length === 0) && (
              <tr>
                <td
                  colSpan={5}
                  className="px-6 py-8 text-center text-ink-muted"
                >
                  Sin fichajes recientes.
                </td>
              </tr>
            )}

            {!loading &&
              sessions?.map((s) => (
                <tr
                  key={s.id}
                  className="hover:bg-surface-muted/50 transition-colors"
                >
                  <td className="px-6 py-3 font-medium text-ink">
                    {s.employee?.full_name ?? s.employee_name ?? `Empleado ${s.employee_id.slice(0, 8)}`}
                  </td>
                  <td className="px-6 py-3 text-ink-muted">
                    {formatDateTime(s.clock_in_time)}
                  </td>
                  <td className="px-6 py-3 text-ink-muted">
                    {s.clock_out_time
                      ? formatDateTime(s.clock_out_time)
                      : "—"}
                  </td>
                  <td className="px-6 py-3 text-ink-muted">
                    {s.total_seconds ? formatSeconds(s.total_seconds) : "—"}
                  </td>
                  <td className="px-6 py-3">
                    {s.is_active ? (
                      <Badge variant="success">Activo</Badge>
                    ) : (
                      <Badge variant="muted">Cerrado</Badge>
                    )}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
