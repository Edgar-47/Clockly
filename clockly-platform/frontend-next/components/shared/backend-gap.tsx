import { Badge } from "@/components/ui/badge";

export function BackendGap({
  title,
  description,
  endpoints,
}: {
  title: string;
  description: string;
  endpoints: string[];
}) {
  return (
    <div className="rounded-lg border border-warning-border bg-warning-bg px-5 py-4 text-sm text-warning">
      <div className="mb-2 flex items-center gap-2">
        <Badge variant="warning">Adapter temporal</Badge>
        <p className="font-semibold text-ink">{title}</p>
      </div>
      <p className="text-ink-muted">{description}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {endpoints.map((endpoint) => (
          <code key={endpoint} className="rounded border border-warning-border bg-white px-2 py-1 text-xs text-ink">
            {endpoint}
          </code>
        ))}
      </div>
    </div>
  );
}
