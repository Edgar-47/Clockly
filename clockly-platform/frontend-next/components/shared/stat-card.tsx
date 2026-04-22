import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  iconColor?: "blue" | "green" | "orange" | "red" | "gray";
  trend?: string;
  loading?: boolean;
}

const iconColorMap = {
  blue: "bg-primary/10 text-primary",
  green: "bg-success-bg text-success",
  orange: "bg-warning-bg text-warning",
  red: "bg-danger-bg text-danger",
  gray: "bg-surface-bg text-ink-muted",
};

export function StatCard({
  label,
  value,
  icon,
  iconColor = "blue",
  trend,
  loading,
}: StatCardProps) {
  if (loading) {
    return (
      <div className="rounded-lg bg-white border border-border shadow-xs p-5">
        <div className="flex items-start justify-between">
          <Skeleton className="h-10 w-10 rounded-lg" />
        </div>
        <Skeleton className="h-4 w-24 mt-4" />
        <Skeleton className="h-7 w-16 mt-2" />
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-white border border-border shadow-xs p-5 transition-shadow hover:shadow-sm">
      <div className="flex items-start justify-between">
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-lg",
            iconColorMap[iconColor],
          )}
        >
          {icon}
        </div>
      </div>
      <p className="mt-4 text-sm font-medium text-ink-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold tracking-tight text-ink">
        {value}
      </p>
      {trend && (
        <p className="mt-1 text-xs text-ink-xmuted">{trend}</p>
      )}
    </div>
  );
}
