"use client";

import { useState } from "react";
import { Topbar } from "@/components/shared/topbar";
import { SessionsTable } from "@/features/attendance/components/sessions-table";
import { useAttendanceHistory } from "@/hooks/use-attendance";
import type { AttendanceHistoryFilters } from "@/types/attendance";

export default function SessionsPage() {
  const [filters, setFilters] = useState<AttendanceHistoryFilters>({});
  const { data, isLoading, error } = useAttendanceHistory(filters);

  return (
    <>
      <Topbar title="Fichajes" />
      <div className="p-8 space-y-6">
        {error && (
          <div className="rounded-lg border border-danger-border bg-danger-bg px-4 py-3 text-sm text-danger">
            Error al cargar los fichajes.
          </div>
        )}
        <SessionsTable
          sessions={data}
          loading={isLoading}
          onFilterChange={setFilters}
        />
      </div>
    </>
  );
}
