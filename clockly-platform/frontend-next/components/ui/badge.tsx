import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide border",
  {
    variants: {
      variant: {
        default: "bg-primary/10 text-primary border-primary/20",
        success: "bg-success-bg text-success border-success-border",
        danger: "bg-danger-bg text-danger border-danger-border",
        warning: "bg-warning-bg text-warning border-warning-border",
        muted: "bg-surface-bg text-ink-muted border-border",
        outline: "border-border-strong text-ink-muted bg-transparent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
