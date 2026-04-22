"use client";

import { useEffect } from "react";
import { Delete, ArrowLeft } from "lucide-react";
import { cn, getInitials } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useKioskStore } from "@/features/kiosk/kiosk.store";
import { useClockIn, useClockOut } from "@/hooks/use-attendance";
import { toast } from "sonner";

const DIGITS = [
  ["1", "2", "3"],
  ["4", "5", "6"],
  ["7", "8", "9"],
  ["", "0", "del"],
];

export function PinPanel() {
  const { selectedEmployee, pin, appendPin, clearPin, reset, setSuccess } =
    useKioskStore();

  const clockIn = useClockIn();
  const clockOut = useClockOut();

  const isClockedIn = selectedEmployee?.is_clocked_in ?? false;
  const employee = selectedEmployee?.employee;

  useEffect(() => {
    if (pin.length === 4) {
      handleClock();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pin]);

  const handleClock = () => {
    if (!selectedEmployee) return;
    const action = isClockedIn ? clockOut : clockIn;
    action.mutate(
      { employee_id: selectedEmployee.employee.id },
      {
        onSuccess: () => {
          setSuccess(isClockedIn ? "out" : "in");
          setTimeout(reset, 3000);
        },
        onError: (err) => {
          toast.error(
            (err as { detail?: string })?.detail ?? "Error al fichar",
          );
          clearPin();
        },
      },
    );
  };

  if (!employee) return null;

  return (
    <div className="flex flex-col items-center gap-8 py-8 animate-slide-up">
      {/* Employee info */}
      <div className="flex flex-col items-center gap-3">
        <div
          className={cn(
            "flex h-20 w-20 items-center justify-center rounded-full text-2xl font-bold",
            isClockedIn
              ? "bg-success/20 text-success"
              : "bg-primary/10 text-primary",
          )}
        >
          {getInitials(employee.first_name, employee.last_name)}
        </div>
        <div className="text-center">
          <p className="text-xl font-bold text-ink">{employee.full_name}</p>
          <p
            className={cn(
              "text-sm font-semibold mt-1",
              isClockedIn ? "text-success" : "text-primary",
            )}
          >
            {isClockedIn ? "Registrar salida" : "Registrar entrada"}
          </p>
        </div>
      </div>

      {/* PIN dots */}
      <div className="flex items-center gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "h-4 w-4 rounded-full border-2 transition-colors duration-100",
              i < pin.length
                ? isClockedIn
                  ? "bg-danger border-danger"
                  : "bg-primary border-primary"
                : "border-border-strong",
            )}
          />
        ))}
      </div>

      {/* Numpad */}
      <div className="grid w-full max-w-xs gap-3">
        {DIGITS.map((row, ri) => (
          <div key={ri} className="grid grid-cols-3 gap-3">
            {row.map((digit, ci) => {
              if (digit === "")
                return <div key={ci} />;
              if (digit === "del")
                return (
                  <button
                    key={ci}
                    onClick={clearPin}
                    className="flex h-16 items-center justify-center rounded-xl border border-border bg-surface-bg text-ink-muted hover:bg-surface-bg-alt transition-colors active:scale-95"
                  >
                    <Delete className="h-5 w-5" />
                  </button>
                );
              return (
                <button
                  key={ci}
                  onClick={() => appendPin(digit)}
                  className="flex h-16 items-center justify-center rounded-xl border border-border bg-white text-xl font-bold text-ink shadow-xs hover:bg-surface-bg hover:shadow-sm transition-all active:scale-95"
                >
                  {digit}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Back */}
      <Button variant="ghost" onClick={reset} className="gap-2">
        <ArrowLeft className="h-4 w-4" />
        Volver
      </Button>
    </div>
  );
}
