import * as React from "react";

import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
};

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex min-h-11 items-center justify-center rounded-xl px-4 py-2.5 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" &&
          "bg-primary text-primary-foreground shadow-subtle hover:bg-primary/92 active:bg-primary/88",
        variant === "secondary" &&
          "border border-border bg-card/92 text-card-foreground hover:bg-muted/80 active:bg-muted",
        variant === "ghost" && "text-foreground hover:bg-muted/75 active:bg-muted",
        className,
      )}
      {...props}
    />
  );
}
