"use client";

import { Users, CheckCircle, XCircle, Clock } from "lucide-react";
import { StatCard } from "@/components/shared/stat-card";
import { formatPercent, formatSeconds } from "@/lib/format";
import type { DashboardSummary } from "@/types/dashboard";

interface MetricsGridProps {
  data?: DashboardSummary;
  loading?: boolean;
}

export function MetricsGrid({ data, loading }: MetricsGridProps) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard
        label="Total empleados"
        value={data?.total_employees ?? 0}
        icon={<Users className="h-5 w-5" />}
        iconColor="blue"
        loading={loading}
      />
      <StatCard
        label="Trabajando ahora"
        value={data?.total_clocked_in ?? 0}
        icon={<CheckCircle className="h-5 w-5" />}
        iconColor="green"
        loading={loading}
      />
      <StatCard
        label="Fuera del turno"
        value={data?.total_clocked_out ?? 0}
        icon={<XCircle className="h-5 w-5" />}
        iconColor="gray"
        loading={loading}
      />
      <StatCard
        label="Horas hoy"
        value={
          data?.kpis ? formatSeconds(data.kpis.total_hours_today) : "—"
        }
        icon={<Clock className="h-5 w-5" />}
        iconColor="orange"
        trend={
          data?.kpis
            ? `Asistencia ${formatPercent(data.kpis.attendance_rate)}`
            : undefined
        }
        loading={loading}
      />
    </div>
  );
}
