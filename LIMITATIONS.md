# Limits of the evidence

- All shipped data and demonstrated defects are synthetic. The controller is deterministic; no live model, external payment processor or customer tenant was exercised.
- The contract covers one full refund or a hold. Partial refunds, multiple currencies, disputes and multi-order production deployments require different business semantics.
- Row counts and SHA-256 digests can establish consistency of the bytes or rows inspected. They cannot establish that an upstream role, filter, cursor or lagging replica exposed every relevant refund.
- The SQLite transaction provides a local snapshot. An external payment ledger, order service and ticket system may settle at different times. A missing independent source or unresolved cutoff requires an inconclusive preflight.
- The reference release is a known-good fixture. A passing reference replay establishes that the local regression distinguishes these variants. Live eligibility history, hidden side effects, real defect rates, customer sign-off and superiority over a competent hand-written assertion suite have not been demonstrated.
