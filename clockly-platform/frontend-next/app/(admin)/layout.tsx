import { Sidebar } from "@/components/shared/sidebar";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-surface-bg">
      <Sidebar />
      <div className="flex-1 pl-[252px]">
        <main className="min-h-screen">{children}</main>
      </div>
    </div>
  );
}
