import * as React from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "w-full rounded-xl border border-input bg-background/80 px-4 py-3 text-sm text-foreground outline-none transition placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50 file:mr-4 file:rounded-lg file:border file:border-border file:bg-muted/80 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-foreground hover:file:bg-muted",
        className,
      )}
      {...props}
    />
  );
}
