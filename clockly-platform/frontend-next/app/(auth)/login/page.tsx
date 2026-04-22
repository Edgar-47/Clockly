import type { Metadata } from "next";
import Link from "next/link";
import { LoginForm } from "@/features/auth/components/login-form";

export const metadata: Metadata = {
  title: "Iniciar sesión",
};

export default function LoginPage() {
  return (
    <div className="rounded-xl border border-border bg-white p-8 shadow-sm">
      <div className="mb-6 text-center">
        <div className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-xs font-bold uppercase tracking-wide text-primary">
          Administrador
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-ink">
          Acceso al Panel
        </h1>
        <p className="mt-1.5 text-sm text-ink-muted">
          Entra con tus credenciales para gestionar tu negocio.
        </p>
      </div>

      <LoginForm />

      <div className="mt-6 text-center">
        <Link
          href="/forgot-password"
          className="text-sm text-ink-muted hover:text-primary transition-colors"
        >
          ¿Olvidaste tu contraseña?
        </Link>
      </div>

      <div className="relative my-5">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-border" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-white px-3 text-ink-xmuted tracking-wider">
            Acceso kiosk
          </span>
        </div>
      </div>

      <Link
        href="/kiosk"
        className="flex items-center justify-center gap-2 rounded-lg border border-border-strong px-4 py-2.5 text-sm font-medium text-ink-muted hover:border-primary hover:text-primary transition-colors"
      >
        Abrir kiosk de fichaje
      </Link>
    </div>
  );
}
