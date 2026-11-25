# Juniper Mile Outfitters (fictional) | Executive case study

**SYNTHETIC SIMULATION — fictional company; no customer outcomes or realized savings.** Monetary amounts are local currency. This is a simulation of the VerityOps verification approach. No customers were served and no money moved.

The fictional retailer sells outdoor accessories through a web shop, marketplace and outlet app. A cancel request may release an uncaptured authorization, while a captured sale can require a refund across two tenders. Paid shipping is excluded from an ordinary return under this fictional policy.

In a February order cohort of **32,000 orders**, 3,670 service tickets required a decision. On the same candidate events, 547 tickets had a true rule or end-state defect. A bot-completed signal plus a successful acknowledgement passed 515 defective tickets. Independent verification flagged **511 of 547** (93.42%); 36 defective tickets lacked sufficient evidence for a verdict. No correct ticket received a verifier FAIL. This result depends on aligned rules and trustworthy identifiers; some correct tickets remained inconclusive.

**Operational consequence.** Review queues moved from 362 to 1,032 tickets. An evidence bundle can make an individual investigation shorter; more investigations can still cost more. Missing readback stays inconclusive after the corrected release unless the source itself is restored.

**Financial interpretation.** Gross synthetic excess postings total USD 8,948.79 under both A and B. Neither workflow stopped a candidate payment. Only a future release gate could change later postings. Base assumptions give USD 1,696.95 of conditional exposure opportunity and a net estimate of **USD -2,833.55** after modeled labor and verification costs. No realized savings are observed or estimated as an accomplished result.

[Detailed matched comparison and case traces](comparison.md) · [Chart of decisions](verdicts.svg) · [Sensitivity chart](economics.svg) · [Machine-readable evidence](dashboard.json) · [Synthetic SQLite database](synthetic.sqlite)
