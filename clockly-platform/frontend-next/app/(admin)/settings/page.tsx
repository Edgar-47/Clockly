"use client";

import { Topbar } from "@/components/shared/topbar";
import { useMe } from "@/hooks/use-auth";

export default function SettingsPage() {
  const me = useMe();
  return (
    <>
      <Topbar title="Configuracion" />
      <div className="space-y-6 p-8">
        <div className="rounded-lg border border-border bg-white p-6 shadow-xs">
          <h2 className="text-lg font-bold text-ink">Empresa activa</h2>
          <dl className="mt-4 grid gap-4 text-sm md:grid-cols-3">
            <div>
              <dt className="text-ink-muted">Nombre</dt>
              <dd className="font-semibold text-ink">{me.data?.company.name ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Slug</dt>
              <dd className="font-semibold text-ink">{me.data?.company.slug ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Zona horaria</dt>
              <dd className="font-semibold text-ink">{me.data?.company.timezone ?? "—"}</dd>
            </div>
          </dl>
        </div>
      </div>
    </>
  );
}
