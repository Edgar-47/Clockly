import { format, formatDistanceToNow, parseISO } from "date-fns";
import { es } from "date-fns/locale";

export function formatDate(iso: string): string {
  return format(parseISO(iso), "dd MMM yyyy", { locale: es });
}

export function formatDateTime(iso: string): string {
  return format(parseISO(iso), "dd MMM · HH:mm", { locale: es });
}

export function formatTime(iso: string): string {
  return format(parseISO(iso), "HH:mm", { locale: es });
}

export function formatRelative(iso: string): string {
  return formatDistanceToNow(parseISO(iso), { addSuffix: true, locale: es });
}

export function formatSeconds(totalSeconds: number): string {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

export function formatHours(hours: number): string {
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}
