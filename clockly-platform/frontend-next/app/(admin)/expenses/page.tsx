import { Topbar } from "@/components/shared/topbar";
import { BackendGap } from "@/components/shared/backend-gap";

export default function ExpensesPage() {
  return (
    <>
      <Topbar title="Gastos" />
      <div className="space-y-6 p-8">
        <BackendGap
          title="Modulo migrado a nivel de UX, pendiente de REST v2"
          description="El frontend viejo incluia listado de gastos, alta, detalle, vista admin, filtros por estado/empleado/concepto/fecha/importe y acciones de aprobacion. La pantalla queda reservada con el adapter tipado para activarla cuando FastAPI v2 exponga el contrato."
          endpoints={["GET /expenses", "POST /expenses", "GET /expenses/admin", "PATCH /expenses/{id}"]}
        />
        <div className="rounded-lg border border-border bg-white p-6 shadow-xs">
          <h2 className="text-lg font-bold text-ink">Flujos a conectar</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {["Mis gastos", "Revision admin", "Reembolsos"].map((item) => (
              <div key={item} className="rounded border border-border bg-surface-muted p-4 text-sm font-medium text-ink">
                {item}
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
