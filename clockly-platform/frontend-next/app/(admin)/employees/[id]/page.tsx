"use client";

import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { Topbar } from "@/components/shared/topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmployeeForm } from "@/features/employees/components/employee-form";
import { useEmployee, useUpdateEmployee } from "@/hooks/use-employees";
import type { EmployeeUpdateRequest } from "@/types/employee";

export default function EmployeeDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const employee = useEmployee(params.id);
  const update = useUpdateEmployee(params.id);

  const handleSubmit = (values: EmployeeUpdateRequest) => {
    update.mutate(values, {
      onSuccess: () => toast.success("Empleado actualizado."),
      onError: () => toast.error("No se pudo actualizar el empleado."),
    });
  };

  return (
    <>
      <Topbar
        title="Editar empleado"
        actions={
          <Button variant="ghost" size="sm" onClick={() => router.push("/employees")}>
            <ArrowLeft className="h-4 w-4" />
            Volver
          </Button>
        }
      />
      <div className="p-8 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle>{employee.data?.full_name ?? "Empleado"}</CardTitle>
            <CardDescription>Actualiza datos personales, puesto, estado y datos de acceso.</CardDescription>
          </CardHeader>
          <CardContent>
            {employee.isLoading && <p className="text-sm text-ink-muted">Cargando empleado...</p>}
            {employee.error && <p className="text-sm text-danger">No se pudo cargar el empleado.</p>}
            {employee.data && (
              <EmployeeForm
                employee={employee.data}
                onSubmit={handleSubmit}
                loading={update.isPending}
                error={update.isError ? "Error al guardar cambios." : null}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
