import type { Metadata } from "next";
import Link from "next/link";
import { Logo } from "@/components/shared/logo";

export const metadata: Metadata = {
  title: "Acceso",
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-surface-bg px-4 py-12">
      <div className="mb-8">
        <Link href="/">
          <Logo size="md" />
        </Link>
      </div>
      <div className="w-full max-w-[420px]">
        {children}
      </div>
      <p className="mt-8 text-xs text-ink-xmuted">
        © {new Date().getFullYear()} ClockLy · Control horario para negocios
      </p>
    </div>
  );
}
