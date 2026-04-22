import Link from "next/link";
import {
  Clock,
  Users,
  BarChart3,
  Shield,
  Smartphone,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import { Logo } from "@/components/shared/logo";

const BENEFITS = [
  {
    icon: Clock,
    title: "Fichaje sin fricción",
    description:
      "Kiosk táctil con PIN para que tus empleados fichen en segundos, sin apps ni móviles.",
  },
  {
    icon: Users,
    title: "Gestión de equipos",
    description:
      "Alta, edición y seguimiento de empleados desde un panel centralizado.",
  },
  {
    icon: BarChart3,
    title: "Informes en tiempo real",
    description:
      "Métricas de asistencia, horas trabajadas e incidencias. Todo actualizado al momento.",
  },
  {
    icon: Shield,
    title: "Control de acceso",
    description:
      "Roles de propietario, administrador y empleado. Cada uno ve solo lo que necesita.",
  },
  {
    icon: Smartphone,
    title: "Optimizado para tablet",
    description:
      "La vista kiosk está diseñada para iPads y tablets de mostrador. Grande, táctil y clara.",
  },
];

const USE_CASES = [
  "Restaurantes y hostelería",
  "Centros de estética",
  "Peluquerías",
  "Gimnasios y fitness",
  "Fisioterapia y salud",
  "Comercio y retail",
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-border bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Logo size="sm" />
          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm font-medium text-ink-muted hover:text-ink transition-colors"
            >
              Acceso admin
            </Link>
            <Link
              href="/kiosk"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:bg-primary-dark transition-colors"
            >
              Abrir kiosk
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden bg-ink px-6 py-24 sm:py-36">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -top-32 -right-32 h-96 w-96 rounded-full bg-primary/20 blur-3xl" />
          <div className="absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-primary/10 blur-3xl" />
        </div>
        <div className="relative mx-auto max-w-4xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-white/70">
            Control horario moderno
          </div>
          <h1 className="text-balance text-5xl font-bold leading-tight tracking-tight text-white sm:text-6xl lg:text-7xl">
            Gestiona tu equipo
            <br />
            <span className="text-primary">sin complicaciones</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-white/60 text-balance">
            ClockLy es el sistema de fichaje y gestión de asistencia pensado
            para negocios locales. Simple para tus empleados, potente para
            ti.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-8 py-4 text-base font-semibold text-white shadow-lg hover:bg-primary-dark transition-all hover:-translate-y-0.5"
            >
              Empezar ahora
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/kiosk"
              className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-8 py-4 text-base font-semibold text-white hover:bg-white/10 transition-colors"
            >
              Ver el kiosk
            </Link>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="bg-surface-bg px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-ink">
              Todo lo que necesitas
            </h2>
            <p className="mt-3 text-lg text-ink-muted">
              Herramientas claras para negocios que valoran su tiempo.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {BENEFITS.map(({ icon: Icon, title, description }) => (
              <div
                key={title}
                className="rounded-xl border border-border bg-white p-6 shadow-xs hover:shadow transition-shadow"
              >
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mb-2 font-bold text-ink">{title}</h3>
                <p className="text-sm text-ink-muted leading-relaxed">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use cases */}
      <section className="bg-white px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
            <div>
              <h2 className="text-3xl font-bold tracking-tight text-ink">
                Hecho para tu tipo de negocio
              </h2>
              <p className="mt-4 text-lg text-ink-muted">
                ClockLy se adapta a la realidad de negocios con equipos de 2
                a 50 personas que necesitan control horario sin burocracia.
              </p>
              <ul className="mt-8 space-y-3">
                {USE_CASES.map((uc) => (
                  <li key={uc} className="flex items-center gap-3">
                    <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-success" />
                    <span className="text-ink-soft font-medium">{uc}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="relative rounded-2xl bg-ink p-8">
              <div className="absolute -top-3 -right-3 rounded-full bg-primary px-3 py-1 text-xs font-bold text-white shadow">
                En vivo
              </div>
              <div className="space-y-3">
                {["María G.", "Carlos P.", "Ana R.", "David M."].map(
                  (name, i) => (
                    <div
                      key={name}
                      className="flex items-center gap-3 rounded-lg bg-white/5 px-4 py-3"
                    >
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-primary text-xs font-bold">
                        {name[0]}
                      </div>
                      <span className="flex-1 text-sm font-medium text-white">
                        {name}
                      </span>
                      <span
                        className={
                          i < 3
                            ? "text-xs font-semibold text-success"
                            : "text-xs font-semibold text-white/40"
                        }
                      >
                        {i < 3 ? "● Fichado" : "○ Libre"}
                      </span>
                    </div>
                  ),
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-primary px-6 py-24">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Empieza hoy mismo
          </h2>
          <p className="mt-4 text-lg text-white/80">
            Sin tarjeta de crédito. Sin setup complicado. Solo entra y empieza
            a gestionar tu equipo.
          </p>
          <Link
            href="/login"
            className="mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-8 py-4 text-base font-bold text-primary hover:bg-white/90 transition-all hover:-translate-y-0.5"
          >
            Acceder al panel
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-white px-6 py-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <Logo size="sm" />
          <p className="text-sm text-ink-xmuted">
            © {new Date().getFullYear()} ClockLy
          </p>
        </div>
      </footer>
    </div>
  );
}
