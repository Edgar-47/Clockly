"use client";

import Link from "next/link";
import { Settings } from "lucide-react";
import { Logo } from "@/components/shared/logo";
import { ClockDisplay } from "@/features/kiosk/components/clock-display";
import { EmployeeGrid } from "@/features/kiosk/components/employee-grid";
import { PinPanel } from "@/features/kiosk/components/pin-panel";
import { SuccessScreen } from "@/features/kiosk/components/success-screen";
import { useKioskStore } from "@/features/kiosk/kiosk.store";
import { useCurrentAttendance } from "@/hooks/use-attendance";
import { Skeleton } from "@/components/ui/skeleton";

export default function KioskPage() {
  const { data: statuses, isLoading } = useCurrentAttendance();
  const step = useKioskStore((s) => s.step);

  const clockedIn = statuses?.filter((s) => s.is_clocked_in).length ?? 0;
  const total = statuses?.length ?? 0;

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border bg-white px-6 py-4">
        <Logo size="sm" />
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 rounded-full bg-surface-bg px-3 py-1.5 text-sm font-medium text-ink-muted border border-border">
            <span className="text-ink-xmuted">{total} empleados</span>
            {clockedIn > 0 && (
              <>
                <span className="text-border-strong">·</span>
                <span className="flex items-center gap-1.5 text-success font-semibold">
                  <span className="h-2 w-2 rounded-full bg-success animate-pulse-dot" />
                  {clockedIn} fichados
                </span>
              </>
            )}
          </div>
          <Link
            href="/login"
            className="rounded-lg p-2 text-ink-xmuted hover:bg-surface-bg hover:text-ink transition-colors"
            title="Acceso admin"
          >
            <Settings className="h-5 w-5" />
          </Link>
        </div>
      </header>

      {/* Body */}
      <main className="flex flex-1 flex-col items-center px-6 py-8 gap-10">
        {/* Clock */}
        <ClockDisplay />

        {/* Content based on step */}
        {step === "grid" && (
          <div className="w-full max-w-5xl">
            <h2 className="mb-6 text-lg font-bold text-ink text-center">
              Selecciona tu nombre para fichar
            </h2>

            {isLoading && (
              <div className="grid grid-cols-3 gap-4 sm:grid-cols-4 lg:grid-cols-5">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-40 rounded-xl" />
                ))}
              </div>
            )}

            {!isLoading && (!statuses || statuses.length === 0) && (
              <div className="rounded-xl border border-border bg-white p-12 text-center">
                <p className="text-ink-muted">
                  No hay empleados activos configurados.
                </p>
                <Link
                  href="/employees/new"
                  className="mt-4 inline-block text-sm text-primary hover:underline"
                >
                  Crear primer empleado →
                </Link>
              </div>
            )}

            {!isLoading && statuses && statuses.length > 0 && (
              <EmployeeGrid statuses={statuses} />
            )}
          </div>
        )}

        {step === "pin" && (
          <div className="w-full max-w-sm">
            <PinPanel />
          </div>
        )}

        {step === "success" && (
          <div className="w-full max-w-sm">
            <SuccessScreen />
          </div>
        )}
      </main>
    </div>
  );
}
