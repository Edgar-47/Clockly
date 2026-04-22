import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Kiosk · ClockLy",
};

export default function KioskLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-surface-bg">
      {children}
    </div>
  );
}
