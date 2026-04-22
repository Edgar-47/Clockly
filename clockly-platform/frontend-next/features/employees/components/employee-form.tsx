"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Employee, EmployeeCreateRequest, EmployeeUpdateRequest } from "@/types/employee";

const schema = z.object({
  first_name: z.string().min(1, "Nombre requerido"),
  last_name: z.string().min(1, "Apellidos requeridos"),
  dni: z.string().optional(),
  password: z.string().min(8, "Minimo 8 caracteres").optional().or(z.literal("")),
  email: z.string().email("Email invalido").optional().or(z.literal("")),
  phone: z.string().optional(),
  role_title: z.string().optional(),
  pin: z
    .string()
    .min(4, "El PIN debe tener al menos 4 digitos")
    .max(12, "Maximo 12 digitos")
    .regex(/^\d*$/, "Solo digitos")
    .optional()
    .or(z.literal("")),
  hired_on: z.string().optional(),
  is_active: z.boolean().default(true),
});

type FormValues = z.infer<typeof schema>;

interface EmployeeFormProps {
  employee?: Employee;
  onSubmit: (values: EmployeeCreateRequest | EmployeeUpdateRequest) => void;
  loading?: boolean;
  error?: string | null;
}

export function EmployeeForm({ employee, onSubmit, loading, error }: EmployeeFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: employee
      ? {
          first_name: employee.first_name,
          last_name: employee.last_name,
          dni: employee.dni ?? "",
          email: employee.email ?? "",
          phone: employee.phone ?? "",
          role_title: employee.role_title ?? "",
          hired_on: employee.hired_on ?? "",
          is_active: employee.is_active,
        }
      : { is_active: true },
  });

  const handleFormSubmit = (values: FormValues) => {
    onSubmit({
      first_name: values.first_name,
      last_name: values.last_name,
      email: values.email || undefined,
      phone: values.phone || undefined,
      dni: values.dni || undefined,
      role_title: values.role_title || undefined,
      hired_on: values.hired_on || undefined,
      password: values.password || undefined,
      pin: values.pin || undefined,
      is_active: values.is_active,
    });
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {error && (
        <div className="rounded-lg border border-danger-border bg-danger-bg px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="first_name">Nombre *</Label>
          <Input id="first_name" placeholder="Maria" {...register("first_name")} />
          {errors.first_name && <p className="text-xs text-danger">{errors.first_name.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="last_name">Apellidos *</Label>
          <Input id="last_name" placeholder="Garcia Lopez" {...register("last_name")} />
          {errors.last_name && <p className="text-xs text-danger">{errors.last_name.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="dni">DNI / NIE</Label>
          <Input id="dni" placeholder="12345678A" {...register("dni")} />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="password">{employee ? "Nueva contrasena" : "Contrasena"}</Label>
          <Input id="password" type="password" placeholder="Minimo 8 caracteres" {...register("password")} />
          {errors.password && <p className="text-xs text-danger">{errors.password.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" placeholder="maria@negocio.com" {...register("email")} />
          {errors.email && <p className="text-xs text-danger">{errors.email.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="phone">Telefono</Label>
          <Input id="phone" placeholder="612 345 678" {...register("phone")} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="space-y-1.5">
          <Label htmlFor="role_title">Puesto</Label>
          <Input id="role_title" placeholder="Estilista, Recepcionista..." {...register("role_title")} />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="pin">PIN kiosk</Label>
          <Input id="pin" placeholder="1234" maxLength={12} {...register("pin")} />
          {errors.pin && <p className="text-xs text-danger">{errors.pin.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="hired_on">Fecha de alta</Label>
          <Input id="hired_on" type="date" {...register("hired_on")} />
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-2">
        <Button type="submit" loading={loading}>
          {employee ? "Guardar cambios" : "Crear empleado"}
        </Button>
      </div>
    </form>
  );
}
