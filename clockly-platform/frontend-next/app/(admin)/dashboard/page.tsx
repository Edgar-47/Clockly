"use client";

import Link from "next/link";
import { MonitorSmartphone } from "lucide-react";
import { Topbar } from "@/components/shared/topbar";
import { Button } from "@/components/ui/button";
import { MetricsGrid } from "@/features/dashboard/components/metrics-grid";
import { ActiveEmployees } from "@/features/dashboard/components/active-employees";
import { RecentSessions } from "@/features/dashboard/components/recent-sessions";
import { useDashboard } from "@/hooks/use-dashboard";

export default function DashboardPage() {
  const { data, isLoading, error } = useDashboard();

  return (
    <>
      <Topbar
        title="Dashboard"
        actions={
          <Button asChild size="sm" variant="secondary">
            <Link href="/kiosk" target="_blank">
              <MonitorSmartphone className="h-4 w-4" />
              Abrir kiosk
            </Link>
          </Button>
        }
      />

      <div className="p-8 space-y-6">
        {error && (
          <div className="rounded-lg border border-danger-border bg-danger-bg px-4 py-3 text-sm text-danger">
            Error al cargar el dashboard. Comprueba la conexión con el backend.
          </div>
        )}

        {data?.business && (
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-ink">
                {data.business.name}
              </h2>
              {data.usage && (
                <p className="text-sm text-ink-muted">
                  Plan{" "}
                  <span className="font-semibold text-ink">
                    {data.usage.plan.name}
                  </span>{" "}
                  · {data.usage.employee_count}/{data.usage.plan.max_employees}{" "}
                  empleados
                </p>
              )}
            </div>
          </div>
        )}

        <MetricsGrid data={data} loading={isLoading} />

        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <RecentSessions
            sessions={data?.recent_sessions}
            loading={isLoading}
          />
          <ActiveEmployees
            statuses={data?.clocked_in_statuses}
            loading={isLoading}
          />
        </div>
      </div>
    </>
  );
}
