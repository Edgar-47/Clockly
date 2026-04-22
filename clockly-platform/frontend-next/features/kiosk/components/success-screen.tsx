"use client";

import { CheckCircle, XCircle } from "lucide-react";
import { useKioskStore } from "@/features/kiosk/kiosk.store";

export function SuccessScreen() {
  const { selectedEmployee, successType } = useKioskStore();
  const employee = selectedEmployee?.employee;
  const isIn = successType === "in";

  return (
    <div className="flex flex-col items-center gap-6 py-16 animate-slide-up">
      <div
        className={
          isIn
            ? "flex h-24 w-24 items-center justify-center rounded-full bg-success-bg text-success"
            : "flex h-24 w-24 items-center justify-center rounded-full bg-danger-bg text-danger"
        }
      >
        {isIn ? (
          <CheckCircle className="h-12 w-12" />
        ) : (
          <XCircle className="h-12 w-12" />
        )}
      </div>

      <div className="text-center">
        <p className="text-3xl font-bold text-ink">
          {isIn ? "¡Bienvenido/a!" : "¡Hasta luego!"}
        </p>
        {employee && (
          <p className="mt-2 text-xl text-ink-muted">{employee.full_name}</p>
        )}
        <p
          className={
            "mt-3 text-base font-semibold " +
            (isIn ? "text-success" : "text-danger")
          }
        >
          {isIn ? "Entrada registrada" : "Salida registrada"}
        </p>
      </div>

      <p className="text-sm text-ink-xmuted">
        Volviendo al inicio en unos segundos…
      </p>
    </div>
  );
}
