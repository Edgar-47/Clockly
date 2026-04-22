"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Search, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { getInitials } from "@/lib/utils";
import { formatDate } from "@/lib/format";
import type { Employee } from "@/types/employee";
import { useSetEmployeeActive } from "@/hooks/use-employees";

interface EmployeeTableProps {
  employees?: Employee[];
  loading?: boolean;
}

const ROLE_LABELS: Record<string, string> = {
  owner: "Propietario",
  admin: "Administrador",
  employee: "Empleado",
};

export function EmployeeTable({ employees, loading }: EmployeeTableProps) {
  const [search, setSearch] = useState("");
  const router = useRouter();
  const setActive = useSetEmployeeActive();

  const filtered = employees?.filter(
    (e) =>
      e.full_name.toLowerCase().includes(search.toLowerCase()) ||
      e.dni?.toLowerCase().includes(search.toLowerCase()) ||
      e.email?.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="rounded-lg border border-border bg-white shadow-xs">
      {/* Header */}
      <div className="flex flex-col gap-3 border-b border-border px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-xmuted" />
          <Input
            placeholder="Buscar empleados..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button
          size="sm"
          onClick={() => router.push("/employees/new")}
        >
          <Plus className="h-4 w-4" />
          Nuevo empleado
        </Button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-muted text-left">
              <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">
                Empleado
              </th>
              <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">
                DNI
              </th>
              <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">
                Rol
              </th>
              <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">
                Estado
              </th>
              <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">
                Alta
              </th>
              <th className="px-6 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {loading &&
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td className="px-6 py-3">
                    <div className="flex items-center gap-3">
                      <Skeleton className="h-8 w-8 rounded-full" />
                      <div className="space-y-1.5">
                        <Skeleton className="h-3.5 w-28" />
                        <Skeleton className="h-3 w-20" />
                      </div>
                    </div>
                  </td>
                  {Array.from({ length: 4 }).map((_, j) => (
                    <td key={j} className="px-6 py-3">
                      <Skeleton className="h-4 w-20" />
                    </td>
                  ))}
                  <td className="px-6 py-3" />
                </tr>
              ))}

            {!loading && filtered?.length === 0 && (
              <tr>
                <td colSpan={6}>
                  <EmptyState
                    title="Sin empleados"
                    description="Crea el primer empleado para empezar."
                    action={{
                      label: "Nuevo empleado",
                      onClick: () => router.push("/employees/new"),
                    }}
                  />
                </td>
              </tr>
            )}

            {!loading &&
              filtered?.map((employee) => (
                <tr
                  key={employee.id}
                  className="hover:bg-surface-muted/50 cursor-pointer transition-colors"
                  onClick={() => router.push(`/employees/${employee.id}`)}
                >
                  <td className="px-6 py-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">
                        {getInitials(employee.first_name, employee.last_name)}
                      </div>
                      <div>
                        <p className="font-semibold text-ink">
                          {employee.full_name}
                        </p>
                        {employee.email && (
                          <p className="text-xs text-ink-muted">
                            {employee.email}
                          </p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-3 text-ink-muted">
                    {employee.dni ?? "—"}
                  </td>
                  <td className="px-6 py-3">
                    <Badge variant="muted">
                      {employee.role_title ?? ROLE_LABELS.employee}
                    </Badge>
                  </td>
                  <td className="px-6 py-3">
                    {employee.is_active ? (
                      <Badge variant="success">Activo</Badge>
                    ) : (
                      <Badge variant="danger">Inactivo</Badge>
                    )}
                  </td>
                  <td className="px-6 py-3 text-ink-muted">
                    {formatDate(employee.created_at)}
                  </td>
                  <td className="px-6 py-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setActive.mutate(
                          { id: employee.id, isActive: !employee.is_active },
                          {
                            onSuccess: () => toast.success("Estado actualizado."),
                            onError: () => toast.error("No se pudo actualizar el empleado."),
                          },
                        );
                      }}
                      className="rounded px-2 py-1 text-xs font-medium text-ink-muted hover:bg-surface-bg hover:text-ink transition-colors"
                    >
                      {employee.is_active ? "Desactivar" : "Activar"}
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {!loading && filtered && (
        <div className="border-t border-border px-6 py-3 text-xs text-ink-muted">
          {filtered.length} empleado{filtered.length !== 1 ? "s" : ""}
          {search && ` (filtrado de ${employees?.length ?? 0})`}
        </div>
      )}
    </div>
  );
}
