"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Building2,
  CalendarDays,
  Clock,
  LayoutDashboard,
  LogOut,
  MonitorSmartphone,
  ReceiptText,
  Settings,
  Shield,
  TicketCheck,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useLogout } from "@/hooks/use-auth";
import { Logo } from "./logo";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Empleados", href: "/employees", icon: Users },
  { label: "Fichajes", href: "/sessions", icon: Clock },
  { label: "Horarios", href: "/schedules", icon: CalendarDays },
  { label: "Analiticas", href: "/analytics", icon: BarChart3 },
  { label: "Incidencias", href: "/tickets", icon: TicketCheck },
  { label: "Gastos", href: "/expenses", icon: ReceiptText },
  { label: "Negocios", href: "/businesses", icon: Building2 },
  { label: "Superadmin", href: "/superadmin", icon: Shield },
  { label: "Configuracion", href: "/settings", icon: Settings },
] as const;

export function Sidebar() {
  const pathname = usePathname();
  const logout = useLogout();

  return (
    <aside className="fixed inset-y-0 left-0 z-40 flex w-[252px] flex-col border-r border-border bg-white">
      <div className="flex h-[70px] items-center border-b border-border px-6">
        <Logo size="sm" />
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-0.5">
          {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
            const active = href === "/dashboard" ? pathname === "/dashboard" : pathname.startsWith(href);
            return (
              <li key={href}>
                <Link
                  href={href}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    active ? "bg-primary/10 text-primary" : "text-ink-muted hover:bg-surface-bg hover:text-ink",
                  )}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="space-y-0.5 border-t border-border p-3">
        <Link
          href="/kiosk"
          target="_blank"
          className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-ink-muted transition-colors hover:bg-surface-bg hover:text-ink"
        >
          <MonitorSmartphone className="h-4 w-4" />
          Abrir Kiosk
        </Link>
        <button
          onClick={() => logout.mutate()}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-ink-muted transition-colors hover:bg-danger-bg hover:text-danger"
        >
          <LogOut className="h-4 w-4" />
          Cerrar sesion
        </button>
      </div>
    </aside>
  );
}
