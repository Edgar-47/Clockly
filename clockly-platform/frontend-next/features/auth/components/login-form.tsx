"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLogin } from "@/hooks/use-auth";

const schema = z.object({
  identifier: z.string().min(1, "Introduce tu usuario o DNI"),
  password: z.string().min(1, "Introduce tu contraseña"),
});

type FormValues = z.infer<typeof schema>;

export function LoginForm() {
  const login = useLogin();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = (values: FormValues) => login.mutate(values);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      {login.error && (
        <div className="flex items-start gap-2.5 rounded-lg border border-danger-border bg-danger-bg px-4 py-3 text-sm text-danger">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>
            {(login.error as { detail?: string })?.detail ??
              "Credenciales incorrectas. Inténtalo de nuevo."}
          </span>
        </div>
      )}

      <div className="space-y-1.5">
        <Label htmlFor="identifier">DNI / Usuario</Label>
        <Input
          id="identifier"
          placeholder="Tu DNI o nombre de usuario"
          autoComplete="username"
          autoFocus
          {...register("identifier")}
          aria-invalid={!!errors.identifier}
        />
        {errors.identifier && (
          <p className="text-xs text-danger">{errors.identifier.message}</p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="password">Contraseña</Label>
        <Input
          id="password"
          type="password"
          placeholder="Tu contraseña"
          autoComplete="current-password"
          {...register("password")}
          aria-invalid={!!errors.password}
        />
        {errors.password && (
          <p className="text-xs text-danger">{errors.password.message}</p>
        )}
      </div>

      <Button
        type="submit"
        className="w-full"
        size="lg"
        loading={login.isPending}
      >
        Entrar al Panel
      </Button>
    </form>
  );
}
