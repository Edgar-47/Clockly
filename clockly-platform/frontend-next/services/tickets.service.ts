import { api } from "@/lib/api-client";
import type { Ticket, TicketCreateRequest, TicketFilters } from "@/types/ticket";

export const ticketsService = {
  list: (filters: TicketFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.employee_id) params.set("employee_id", filters.employee_id);
    if (filters.date_from) params.set("date_from", filters.date_from);
    if (filters.date_to) params.set("date_to", filters.date_to);
    const qs = params.toString();
    return api.get<Ticket[]>(`/tickets${qs ? `?${qs}` : ""}`);
  },

  create: (payload: TicketCreateRequest) => api.post<Ticket>("/tickets", payload),
};
