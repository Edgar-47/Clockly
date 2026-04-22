"use client";

import { toast } from "sonner";
import { Topbar } from "@/components/shared/topbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { TicketForm } from "@/features/tickets/components/ticket-form";
import { TicketsTable } from "@/features/tickets/components/tickets-table";
import { useCreateTicket, useTickets } from "@/hooks/use-tickets";
import type { TicketCreateRequest } from "@/types/ticket";

export default function TicketsPage() {
  const tickets = useTickets();
  const create = useCreateTicket();

  const handleCreate = (values: TicketCreateRequest) => {
    create.mutate(values, {
      onSuccess: () => toast.success("Incidencia creada."),
      onError: () => toast.error("No se pudo crear la incidencia."),
    });
  };

  return (
    <>
      <Topbar title="Incidencias" />
      <div className="grid gap-6 p-8 xl:grid-cols-[380px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Nueva incidencia</CardTitle>
            <CardDescription>Registra tickets internos, ausencias o notas operativas.</CardDescription>
          </CardHeader>
          <CardContent>
            <TicketForm onSubmit={handleCreate} loading={create.isPending} />
          </CardContent>
        </Card>
        <TicketsTable tickets={tickets.data} loading={tickets.isLoading} />
      </div>
    </>
  );
}
