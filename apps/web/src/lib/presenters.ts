export function frictionVariant(label: string | null | undefined): "high" | "medium" | "low" {
  if (label === "high") return "high";
  if (label === "medium") return "medium";
  return "low";
}

export function formatDifficulty(value: unknown): string {
  if (typeof value === "number") {
    return value.toFixed(2);
  }
  return "–";
}
