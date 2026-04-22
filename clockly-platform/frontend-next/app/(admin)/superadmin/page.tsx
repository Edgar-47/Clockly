import { Topbar } from "@/components/shared/topbar";
import { BackendGap } from "@/components/shared/backend-gap";

export default function SuperadminPage() {
  return (
    <>
      <Topbar title="Superadmin" />
      <div className="space-y-6 p-8">
        <BackendGap
          title="Consola SaaS detectada en el frontend viejo"
          description="Hay login superadmin, dashboard, negocios, usuarios, planes, suscripciones, facturacion, metricas, ajustes, auditoria e impersonacion. No se conecta hasta exponer rutas v2 equivalentes y permisos separados."
          endpoints={["/superadmin/*", "GET /plans", "GET /subscriptions", "POST /impersonation"]}
        />
        <div className="grid gap-4 md:grid-cols-3">
          {["Negocios y usuarios", "Planes y billing", "Auditoria e impersonacion"].map((item) => (
            <div key={item} className="rounded-lg border border-border bg-white p-5 shadow-xs">
              <p className="font-semibold text-ink">{item}</p>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
