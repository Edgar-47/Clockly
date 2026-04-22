import { Topbar } from "@/components/shared/topbar";
import { BackendGap } from "@/components/shared/backend-gap";

export default function SchedulesPage() {
  return (
    <>
      <Topbar title="Horarios" />
      <div className="space-y-6 p-8">
        <BackendGap
          title="Horarios detectados y pendientes de REST v2"
          description="La UI historica tenia listado, detalle, creacion, edicion, dias por semana, descanso, horas netas y conteo de empleados asignados. Se conserva el punto de navegacion y el adapter esperado."
          endpoints={["GET /schedules", "POST /schedules", "GET /schedules/{id}", "PATCH /schedules/{id}", "POST /employees/{id}/schedule"]}
        />
      </div>
    </>
  );
}
