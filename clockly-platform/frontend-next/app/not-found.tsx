import Link from "next/link";
import { Logo } from "@/components/shared/logo";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-surface-bg px-6 text-center">
      <Logo size="md" className="mb-8" />
      <p className="text-7xl font-bold text-border-strong">404</p>
      <h1 className="mt-4 text-2xl font-bold text-ink">Página no encontrada</h1>
      <p className="mt-2 text-ink-muted">
        La página que buscas no existe o ha sido movida.
      </p>
      <Link
        href="/dashboard"
        className="mt-8 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-white hover:bg-primary-dark transition-colors"
      >
        Ir al dashboard
      </Link>
    </div>
  );
}
