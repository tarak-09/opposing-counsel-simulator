import * as React from "react";

import { cn } from "@/lib/utils";

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  variant?: "neutral" | "high" | "medium" | "low" | "decision";
};

export function Badge({ className, variant = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em]",
        variant === "neutral" && "border-border/80 bg-muted/70 text-foreground/80",
        variant === "high" && "border-rose-500/30 bg-rose-500/15 text-rose-100",
        variant === "medium" && "border-amber-500/30 bg-amber-500/15 text-amber-100",
        variant === "low" && "border-emerald-500/30 bg-emerald-500/15 text-emerald-100",
        variant === "decision" && "border-sky-500/30 bg-sky-500/15 text-sky-100",
        className,
      )}
      {...props}
    />
  );
}
