import { describe, expect, it } from "vitest";

import { formatDifficulty, frictionVariant } from "@/lib/presenters";

describe("presenters", () => {
  it("maps friction labels to badge variants", () => {
    expect(frictionVariant("high")).toBe("high");
    expect(frictionVariant("medium")).toBe("medium");
    expect(frictionVariant("low")).toBe("low");
    expect(frictionVariant(undefined)).toBe("low");
  });

  it("formats difficulty scores consistently", () => {
    expect(formatDifficulty(0.734)).toBe("0.73");
    expect(formatDifficulty(null)).toBe("–");
  });
});
