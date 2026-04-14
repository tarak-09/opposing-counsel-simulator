import { describe, expect, it } from "vitest";

import { runDemo, seedDemoData } from "@/lib/demo-engine";

describe("demo engine", () => {
  it("seeds realistic demo data with a default persona", () => {
    const seed = seedDemoData();

    expect(seed.matterName).toContain("Nimbus");
    expect(seed.defaultPersona.slug).toBe("startup-counsel");
    expect(seed.originalContract).toContain("Limitation of Liability");
    expect(seed.revisedContract).toContain("Customer may terminate this Agreement for convenience");
  });

  it("runs a complete local demo workflow with changed clauses and evidence", async () => {
    const bundle = await runDemo();

    expect(bundle.runStatus.run.status).toBe("completed");
    expect(bundle.runSummary.overview.total_changed_clauses).toBe(5);
    expect(bundle.runSummary.overview.likely_pushback_count).toBeGreaterThan(2);
    expect(bundle.clauseResults.results).toHaveLength(5);
    expect(bundle.clauseResults.results.every((result) => result.retrieval_hits.length >= 1)).toBe(true);

    const issueTypes = bundle.clauseResults.results.map((result) => result.clause_change.issue_type);
    expect(issueTypes).toEqual(
      expect.arrayContaining([
        "payment_terms",
        "confidentiality",
        "limitation_of_liability",
        "indemnity",
        "termination",
      ]),
    );
  });
});

