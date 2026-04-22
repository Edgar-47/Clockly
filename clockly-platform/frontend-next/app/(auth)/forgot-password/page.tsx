"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const schema = z.object({
  email: z.string().email("Introduce un email válido"),
});
type FormValues = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (_: FormValues) => {
    // TODO: connect to /auth/forgot-password when backend endpoint is ready
    await new Promise((r) => setTimeout(r, 800));
    setSent(true);
  };

  return (
    <div className="rounded-xl border border-border bg-white p-8 shadow-sm">
      {sent ? (
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-success-bg text-success">
            <Mail className="h-7 w-7" />
          </div>
          <h1 className="text-xl font-bold text-ink">
            Revisa tu correo
          </h1>
          <p className="mt-2 text-sm text-ink-muted">
            Si tu email está registrado, recibirás un enlace para recuperar tu
            contraseña.
          </p>
          <Link
            href="/login"
            className="mt-6 inline-flex items-center gap-2 text-sm text-primary hover:underline"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver al login
          </Link>
        </div>
      ) : (
        <>
          <div className="mb-6">
            <h1 className="text-2xl font-bold tracking-tight text-ink">
              Recuperar contraseña
            </h1>
            <p className="mt-1.5 text-sm text-ink-muted">
              Introduce tu email y te enviaremos un enlace de recuperación.
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="tu@negocio.com"
                autoFocus
                {...register("email")}
              />
              {errors.email && (
                <p className="text-xs text-danger">{errors.email.message}</p>
              )}
            </div>
            <Button
              type="submit"
              className="w-full"
              loading={isSubmitting}
            >
              Enviar enlace
            </Button>
          </form>

          <Link
            href="/login"
            className="mt-5 flex items-center justify-center gap-2 text-sm text-ink-muted hover:text-ink transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver al login
          </Link>
        </>
      )}
    </div>
  );
}
