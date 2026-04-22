"use client";

import { Topbar } from "@/components/shared/topbar";
import { BackendGap } from "@/components/shared/backend-gap";
import { StatCard } from "@/components/shared/stat-card";
import { useDashboard } from "@/hooks/use-dashboard";
import { formatSeconds } from "@/lib/format";
import { BarChart3, Clock, Users } from "lucide-react";

export default function AnalyticsPage() {
  const dashboard = useDashboard();
  const kpis = dashboard.data?.kpis;

  return (
    <>
      <Topbar title="Analiticas" />
      <div className="space-y-6 p-8">
        <div className="grid gap-4 md:grid-cols-3">
          <StatCard
            label="Horas periodo"
            value={kpis ? formatSeconds(kpis.total_hours_month) : "—"}
            icon={<Clock className="h-5 w-5" />}
            iconColor="blue"
            loading={dashboard.isLoading}
          />
          <StatCard
            label="Top trabajador"
            value={kpis?.top_worker_this_week ?? "Sin datos"}
            icon={<Users className="h-5 w-5" />}
            iconColor="green"
            loading={dashboard.isLoading}
          />
          <StatCard
            label="Sesiones abiertas"
            value={dashboard.data?.total_clocked_in ?? 0}
            icon={<BarChart3 className="h-5 w-5" />}
            iconColor="orange"
            loading={dashboard.isLoading}
          />
        </div>
        <BackendGap
          title="Analiticas avanzadas preparadas"
          description="El frontend viejo incluia ranking, filtros por periodo/empleado, tendencia de horas extra, heatmap y planificado vs real. FastAPI v2 solo expone /metrics/overview por ahora; la pantalla ya consume esos datos y marca los contratos pendientes."
          endpoints={["GET /metrics/overview", "GET /metrics/ranking", "GET /metrics/heatmap", "GET /metrics/planned-vs-actual"]}
        />
      </div>
    </>
  );
}
