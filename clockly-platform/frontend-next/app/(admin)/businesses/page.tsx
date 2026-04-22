import { Topbar } from "@/components/shared/topbar";
import { BackendGap } from "@/components/shared/backend-gap";

export default function BusinessesPage() {
  return (
    <>
      <Topbar title="Negocios" />
      <div className="space-y-6 p-8">
        <BackendGap
          title="Selector y administracion de negocios pendientes de backend v2"
          description="El frontend viejo tenia listado, creacion, cambio de negocio activo y ajustes de negocio. FastAPI v2 ya trabaja por company/tenant, pero aun no expone endpoints de gestion para esta pantalla."
          endpoints={["GET /businesses", "POST /businesses", "PATCH /businesses/{id}", "POST /businesses/{id}/select"]}
        />
        <div className="rounded-lg border border-border bg-white p-6 shadow-xs">
          <h2 className="text-lg font-bold text-ink">Paridad funcional prevista</h2>
          <p className="mt-2 text-sm text-ink-muted">
            Listado de negocios, alta de nuevo negocio, configuracion fiscal/operativa y cambio de contexto tenant.
          </p>
        </div>
      </div>
    </>
  );
}
