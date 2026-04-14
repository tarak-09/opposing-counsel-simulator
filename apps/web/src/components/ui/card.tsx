import * as React from "react";

import { cn } from "@/lib/utils";

type CardProps = React.HTMLAttributes<HTMLDivElement> & {
  tone?: "default" | "muted" | "inset" | "ghost";
  padding?: "sm" | "md" | "lg";
};

export function Card({ className, tone = "default", padding = "md", ...props }: CardProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-[24px] border backdrop-blur-sm before:pointer-events-none before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-foreground/10 before:to-transparent",
        tone === "default" && "border-border/90 bg-card/95 text-card-foreground shadow-panel",
        tone === "muted" && "border-border/75 bg-muted/38 text-card-foreground shadow-subtle",
        tone === "inset" && "border-border/65 bg-background/78 text-foreground",
        tone === "ghost" && "border-border/60 bg-background/30 text-foreground",
        padding === "sm" && "p-4",
        padding === "md" && "p-5",
        padding === "lg" && "p-6",
        className,
      )}
      {...props}
    />
  );
}
