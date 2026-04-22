"use client";

import { Topbar } from "@/components/shared/topbar";
import { EmployeeTable } from "@/features/employees/components/employee-table";
import { useEmployees } from "@/hooks/use-employees";

export default function EmployeesPage() {
  const { data, isLoading, error } = useEmployees();

  return (
    <>
      <Topbar title="Empleados" />
      <div className="p-8 space-y-6">
        {error && (
          <div className="rounded-lg border border-danger-border bg-danger-bg px-4 py-3 text-sm text-danger">
            Error al cargar empleados.
          </div>
        )}
        <EmployeeTable employees={data} loading={isLoading} />
      </div>
    </>
  );
}
