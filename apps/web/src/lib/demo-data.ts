import type { Persona } from "@ocs/schemas";

const demoTimestamp = "2026-04-13T12:00:00.000Z";

export const demoMatterName = "Nimbus Analytics Subscription Agreement";
export const demoDefaultPersonaSlug = "startup-counsel";

export const demoOriginalContract = `MASTER SUBSCRIPTION AGREEMENT

1. Payment Terms. Customer will pay undisputed invoices within thirty (30) days after receipt. Vendor may suspend access to the Services if an undisputed invoice remains unpaid for more than fifteen (15) days after written notice.

2. Confidentiality. Each party will protect the other party's Confidential Information using at least reasonable care and will not disclose such information except to its employees, contractors, and advisors who have a need to know and are bound by written confidentiality obligations. Confidentiality obligations survive for three (3) years after termination, except for trade secrets, which remain protected for so long as they qualify as trade secrets under applicable law.

3. Limitation of Liability. Except for fraud, willful misconduct, or a party's breach of Section 2 (Confidentiality), each party's aggregate liability arising out of or related to this Agreement will not exceed the fees paid or payable by Customer under this Agreement during the twelve (12) months preceding the event giving rise to the claim. Neither party will be liable for any indirect, incidental, special, or consequential damages.

4. Indemnity. Vendor will defend Customer against any third-party claim alleging that the Services infringe that third party's intellectual property rights, and Vendor will indemnify Customer against any damages, costs, and reasonable attorneys' fees finally awarded by a court or agreed in settlement by Vendor. Customer will promptly notify Vendor of the claim and provide reasonable cooperation.

5. Term and Termination. The initial subscription term is twelve (12) months and will automatically renew for successive one-year terms unless either party gives at least thirty (30) days' notice of non-renewal before the end of the then-current term. Either party may terminate this Agreement for material breach if the breach remains uncured for thirty (30) days after written notice.`;

export const demoRevisedContract = `MASTER SUBSCRIPTION AGREEMENT

1. Payment Terms. Customer will pay undisputed invoices within forty-five (45) days after receipt. Customer may withhold any disputed amount until the parties resolve the dispute in good faith. Vendor may not suspend the Services unless an undisputed invoice remains unpaid for more than forty-five (45) days after written notice to Customer's finance contact.

2. Confidentiality. Each party will protect the other party's Confidential Information using no less than industry-standard safeguards and will not disclose such information except to personnel with a strict need to know. Vendor may not use Customer Confidential Information for analytics, benchmarking, or model training without Customer's prior written consent. Confidentiality obligations survive for five (5) years after termination, and Customer may seek injunctive relief for any threatened or actual unauthorized use or disclosure.

3. Limitation of Liability. Except for Customer's payment obligations, each party's aggregate liability arising out of or related to this Agreement will not exceed two (2) times the fees paid or payable by Customer under this Agreement during the twelve (12) months preceding the event giving rise to the claim. The foregoing cap will not apply to breaches of confidentiality, data security incidents, privacy violations, indemnity obligations, gross negligence, or willful misconduct. Neither party will be liable for any indirect, incidental, special, or consequential damages.

4. Indemnity. Vendor will defend, indemnify, and hold harmless Customer, its affiliates, and their respective officers, directors, employees, and contractors from and against any third-party claim, demand, investigation, or proceeding arising from or relating to (a) alleged infringement or misappropriation by the Services, (b) Vendor's breach of confidentiality obligations, (c) any security incident or violation of data protection law attributable to Vendor, or (d) bodily injury, death, or tangible property damage caused by Vendor. Vendor's indemnity obligations will be in addition to, and not limited by, any limitation of liability in this Agreement.

5. Term and Termination. The initial subscription term is twelve (12) months and will automatically renew for successive one-year terms unless either party gives at least sixty (60) days' notice of non-renewal before the end of the then-current term. Customer may terminate this Agreement for convenience on thirty (30) days' written notice after the first ninety (90) days of the initial term. Either party may terminate this Agreement for material breach if the breach remains uncured for fifteen (15) days after written notice. Upon any expiration or termination, Vendor will provide transition assistance for up to sixty (60) days at no additional charge.`;

export const demoPlaybook = `NEGOTIATION PLAYBOOK

1. Liability. Standard liability is 6-12 months of fees. Enterprise customers often ask for 24 months or uncapped indemnity, but vendor fallback should be 12 months of fees with narrow carve-outs for fraud, willful misconduct, and a limited confidentiality/data protection exception.

2. Indemnity. Indemnity should be mutual for SaaS contracts. Vendor should resist uncapped indemnity for data incidents or open-ended coverage for investigations, bodily injury, or property damage unless those obligations are tied to clear operational risk and supported by insurance.

3. Payment Terms. Net 30 for undisputed invoices is standard. Net 45 may be acceptable only for strategic accounts and should not include an open-ended right to withhold payment or delay service suspension indefinitely.

4. Termination. Avoid customer termination for convenience during the committed subscription term unless stranded implementation costs are recovered. Maintain at least a 30-day cure period for material breach.

5. Confidentiality. Permit use of de-identified service data for analytics. Do not accept blanket bans on internal service improvement or injunctive relief language that expands remedies beyond standard equitable relief principles.`;

export const demoPrecedent = `VENDOR PRECEDENT NOTES

1. Liability Benchmark. Vendor-friendly SaaS paper commonly caps liability at fees paid in the prior 12 months, with 6-12 months of fees as the usual negotiation band for middle-market deals.

2. Indemnity Benchmark. Indemnity should be mutual for SaaS contracts where each party controls its own intellectual property, data handling, and personnel. Third-party claims remain the standard trigger.

3. Payment Benchmark. Net 30 from receipt of invoice remains the most common standard. Suspension rights typically require written notice and only apply to undisputed overdue amounts.

4. Termination Benchmark. Customer termination for convenience is uncommon in annual subscription deals unless paired with a termination fee, notice buffer, or limited post-go-live window.

5. Confidentiality Benchmark. Confidentiality obligations usually survive three to five years, and analytics use is generally acceptable if the data is aggregated and de-identified.`;

export const demoFallback = `APPROVED FALLBACK CLAUSES

1. Liability Fallback. Except for fraud, willful misconduct, and each party's indemnity obligations for third-party intellectual property claims, each party's aggregate liability under this Agreement will not exceed the fees paid or payable in the 12 months preceding the event giving rise to the claim. A limited carve-out for confidentiality and data protection obligations may apply, but any such carve-out should be subject to a separate super-cap.

2. Mutual Indemnity Fallback. Each party will defend the other party against third-party claims alleging that such party's technology, content, or data violates applicable law or infringes a third party's intellectual property rights, and each party will pay damages finally awarded or agreed in settlement. Indemnity obligations should remain tied to third-party claims and proportionate to the risk controlled by the indemnifying party.

3. Payment Fallback. Customer will pay undisputed invoices within thirty (30) days after receipt. Customer may withhold only the specifically disputed portion of an invoice, and the parties will work in good faith to resolve the dispute promptly.

4. Termination Fallback. Either party may terminate for material breach if the breach remains uncured for thirty (30) days after written notice. Customer termination for convenience during the initial subscription term requires at least sixty (60) days' notice and payment of all committed fees through the effective termination date.

5. Confidentiality Fallback. Each party may use de-identified service data for internal analytics and product improvement, provided such use does not identify the other party or circumvent confidentiality obligations.`;

export const demoPersonas: Persona[] = [
  {
    id: "d6f8f29d-72d0-4d96-8f0d-d6f9182f2901",
    created_at: demoTimestamp,
    updated_at: demoTimestamp,
    slug: "aggressive-procurement",
    name: "Aggressive Procurement",
    description:
      "A buyer-side procurement team that pushes for maximum leverage, stronger customer protections, and broad remedies before signing.",
    risk_tolerance: 2,
    leverage: 5,
    speed_priority: 2,
    privacy_sensitivity: 5,
    liability_strictness: 5,
    fallback_flexibility: 2,
    tone: "firm and exacting",
    issue_positions: {
      limitation_of_liability: {
        non_negotiable: true,
        fallback_clause:
          "Customer needs at least a 24-month cap with carve-outs for confidentiality, security incidents, privacy breaches, indemnity obligations, and willful misconduct.",
      },
      indemnity: {
        non_negotiable: true,
        fallback_clause:
          "Vendor should defend and indemnify Customer for IP, data protection, confidentiality, and security incident claims caused by Vendor.",
      },
    },
    is_builtin: true,
    is_active: true,
  },
  {
    id: "9ae65f62-7290-48f6-bb82-2f0f3cc8847b",
    created_at: demoTimestamp,
    updated_at: demoTimestamp,
    slug: "big-tech-legal",
    name: "Big Tech Legal",
    description:
      "A scaled in-house legal team balancing policy discipline, precedent consistency, and cross-functional review requirements.",
    risk_tolerance: 3,
    leverage: 4,
    speed_priority: 3,
    privacy_sensitivity: 5,
    liability_strictness: 5,
    fallback_flexibility: 3,
    tone: "measured and policy-driven",
    issue_positions: {
      limitation_of_liability: {
        non_negotiable: true,
        fallback_clause:
          "Aggregate liability remains capped at fees paid or payable in the preceding twelve months, except for fraud, willful misconduct, infringement indemnity, and breaches of confidentiality or data protection obligations.",
      },
      confidentiality: {
        non_negotiable: true,
        fallback_clause:
          "Customer confidential information cannot be used for analytics or product improvement without express approval.",
      },
    },
    is_builtin: true,
    is_active: true,
  },
  {
    id: "f0ae22e4-58d8-4d54-95e0-6d03fd0ed912",
    created_at: demoTimestamp,
    updated_at: demoTimestamp,
    slug: "startup-counsel",
    name: "Startup Counsel",
    description:
      "Vendor-side counsel for a fast-moving startup that prioritizes closing the deal quickly while protecting balance-sheet, indemnity, and operational risk.",
    risk_tolerance: 4,
    leverage: 2,
    speed_priority: 5,
    privacy_sensitivity: 4,
    liability_strictness: 4,
    fallback_flexibility: 5,
    tone: "pragmatic and commercially focused",
    issue_positions: {
      limitation_of_liability: {
        non_negotiable: true,
        fallback_clause:
          "Vendor liability should remain within a 12-month fee cap, with any confidentiality or data protection carve-out subject to a narrow super-cap.",
      },
      termination: {
        non_negotiable: false,
        fallback_clause:
          "Either party may terminate for material breach after a 30-day cure period, but customer convenience termination during the initial term requires notice and payment of committed fees.",
      },
      payment_terms: {
        non_negotiable: false,
        fallback_clause:
          "Invoices are due net 30, disputed amounts are carved out specifically, and suspension applies only to undisputed overdue amounts after notice.",
      },
    },
    is_builtin: true,
    is_active: true,
  },
];

