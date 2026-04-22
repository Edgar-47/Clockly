"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { Topbar } from "@/components/shared/topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { EmployeeForm } from "@/features/employees/components/employee-form";
import { useCreateEmployee } from "@/hooks/use-employees";
import type { EmployeeCreateRequest, EmployeeUpdateRequest } from "@/types/employee";

export default function NewEmployeePage() {
  const router = useRouter();
  const create = useCreateEmployee();

  const handleSubmit = (values: EmployeeCreateRequest | EmployeeUpdateRequest) => {
    create.mutate(values as EmployeeCreateRequest, {
      onSuccess: (employee) => {
        toast.success(`Empleado ${employee.full_name} creado correctamente.`);
        router.push("/employees");
      },
      onError: (err) => {
        toast.error(
          (err as { detail?: string })?.detail ?? "Error al crear el empleado.",
        );
      },
    });
  };

  return (
    <>
      <Topbar
        title="Nuevo empleado"
        actions={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/employees")}
          >
            <ArrowLeft className="h-4 w-4" />
            Volver
          </Button>
        }
      />
      <div className="p-8 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle>Datos del empleado</CardTitle>
            <CardDescription>
              Rellena los campos para dar de alta al nuevo empleado.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <EmployeeForm
              onSubmit={handleSubmit}
              loading={create.isPending}
              error={
                create.isError
                  ? ((create.error as { detail?: string })?.detail ??
                    "Error inesperado")
                  : null
              }
            />
          </CardContent>
        </Card>
      </div>
    </>
  );
}
