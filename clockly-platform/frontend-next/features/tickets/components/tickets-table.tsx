"use client";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/format";
import type { Ticket } from "@/types/ticket";

const STATUS_LABELS: Record<string, string> = {
  open: "Abierta",
  in_progress: "En curso",
  resolved: "Resuelta",
  closed: "Cerrada",
};

export function TicketsTable({ tickets, loading }: { tickets?: Ticket[]; loading?: boolean }) {
  return (
    <div className="rounded-lg border border-border bg-white shadow-xs">
      <div className="border-b border-border px-6 py-4">
        <h2 className="font-bold text-ink">Incidencias ({tickets?.length ?? 0})</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-muted text-left">
              {["Titulo", "Fecha", "Estado", "Descripcion"].map((header) => (
                <th key={header} className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {loading &&
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 4 }).map((__, j) => (
                    <td key={j} className="px-6 py-3">
                      <Skeleton className="h-4 w-28" />
                    </td>
                  ))}
                </tr>
              ))}
            {!loading && (!tickets || tickets.length === 0) && (
              <tr>
                <td colSpan={4} className="px-6 py-10 text-center text-sm text-ink-muted">
                  No hay incidencias registradas.
                </td>
              </tr>
            )}
            {!loading &&
              tickets?.map((ticket) => (
                <tr key={ticket.id} className="hover:bg-surface-muted/50">
                  <td className="px-6 py-3 font-semibold text-ink">{ticket.title}</td>
                  <td className="px-6 py-3 text-ink-muted">
                    {ticket.occurred_on ? formatDate(ticket.occurred_on) : formatDate(ticket.created_at)}
                  </td>
                  <td className="px-6 py-3">
                    <Badge variant={ticket.status === "open" ? "warning" : "muted"}>
                      {STATUS_LABELS[ticket.status] ?? ticket.status}
                    </Badge>
                  </td>
                  <td className="max-w-md px-6 py-3 text-ink-muted">
                    {ticket.description ?? "-"}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
