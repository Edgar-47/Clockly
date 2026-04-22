export type TicketStatus = "open" | "in_progress" | "resolved" | "closed";

export interface Ticket {
  id: string;
  company_id: string;
  employee_id: string | null;
  user_id: string | null;
  title: string;
  description: string | null;
  status: TicketStatus;
  occurred_on: string | null;
  attachment_key: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketCreateRequest {
  employee_id?: string;
  title: string;
  description?: string;
  occurred_on?: string;
  attachment_key?: string;
}

export interface TicketFilters {
  employee_id?: string;
  date_from?: string;
  date_to?: string;
}
