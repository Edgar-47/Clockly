"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDateTime, formatSeconds } from "@/lib/format";
import type { SessionReport, AttendanceHistoryFilters } from "@/types/attendance";
import { attendanceService } from "@/services/attendance.service";

interface SessionsTableProps {
  sessions?: SessionReport[];
  loading?: boolean;
  onFilterChange: (filters: AttendanceHistoryFilters) => void;
}

const INCIDENT_LABELS: Record<string, string> = {
  late_arrival: "Llegada tarde",
  early_departure: "Salida anticipada",
  absence: "Ausencia",
  overtime: "Horas extra",
};

export function SessionsTable({
  sessions,
  loading,
  onFilterChange,
}: SessionsTableProps) {
  const [filters, setFilters] = useState<AttendanceHistoryFilters>({});

  const applyFilter = (update: Partial<AttendanceHistoryFilters>) => {
    const next = { ...filters, ...update };
    setFilters(next);
    onFilterChange(next);
  };

  return (
    <div className="rounded-lg border border-border bg-white shadow-xs">
      {/* Filters */}
      <div className="flex flex-wrap gap-3 border-b border-border px-6 py-4">
        <Input
          type="date"
          className="w-auto"
          onChange={(e) => applyFilter({ date_from: e.target.value || undefined })}
        />
        <Input
          type="date"
          className="w-auto"
          onChange={(e) => applyFilter({ date_to: e.target.value || undefined })}
        />
        <Select
          onValueChange={(v) =>
            applyFilter({
              status: v === "all" ? undefined : v === "open" ? "open" : "closed",
            })
          }
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="open">Activas</SelectItem>
            <SelectItem value="closed">Cerradas</SelectItem>
          </SelectContent>
        </Select>
        <Select
          onValueChange={(v) =>
            applyFilter({ incident_filter: v === "all" ? undefined : v })
          }
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Incidencia" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            <SelectItem value="late_arrival">Llegada tarde</SelectItem>
            <SelectItem value="early_departure">Salida anticipada</SelectItem>
            <SelectItem value="overtime">Horas extra</SelectItem>
          </SelectContent>
        </Select>
        <div className="ml-auto flex gap-2">
          <Button variant="secondary" size="sm" asChild>
            <a href={attendanceService.exportUrl("excel", filters)}>Excel</a>
          </Button>
          <Button variant="secondary" size="sm" asChild>
            <a href={attendanceService.exportUrl("pdf", filters)}>PDF</a>
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-muted text-left">
              {["Empleado", "Entrada", "Salida", "Duración", "Incidencia", "Estado"].map(
                (h) => (
                  <th
                    key={h}
                    className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-ink-muted"
                  >
                    {h}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {loading &&
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <td key={j} className="px-6 py-3">
                      <Skeleton className="h-4 w-24" />
                    </td>
                  ))}
                </tr>
              ))}

            {!loading && (!sessions || sessions.length === 0) && (
              <tr>
                <td
                  colSpan={6}
                  className="px-6 py-10 text-center text-sm text-ink-muted"
                >
                  No hay fichajes con los filtros seleccionados.
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
                    {s.clock_out_time ? formatDateTime(s.clock_out_time) : "—"}
                  </td>
                  <td className="px-6 py-3 text-ink-muted">
                    {s.total_seconds ? formatSeconds(s.total_seconds) : "—"}
                  </td>
                  <td className="px-6 py-3">
                    {s.incident_type ? (
                      <Badge variant="warning">
                        {INCIDENT_LABELS[s.incident_type] ?? s.incident_type}
                      </Badge>
                    ) : (
                      <span className="text-ink-xmuted">—</span>
                    )}
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

      {!loading && sessions && (
        <div className="border-t border-border px-6 py-3 text-xs text-ink-muted">
          {sessions.length} registro{sessions.length !== 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}
