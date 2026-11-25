# 青栖集家居（虚构） / Qingqi Home (fictional) | Executive case study

**SYNTHETIC SIMULATION — fictional company; no customer outcomes or realized savings.** Monetary amounts are local currency. This is a simulation of the VerityOps verification approach. No customers were served and no money moved.

The fictional home-goods retailer operates a flagship marketplace, live-commerce storefront and mini-store. Its return, refund-only and price-protection queues follow separate eligibility rules. Platform subsidies do not go back to the shopper. Platform-balance postings clear on a daily China-local batch; wallet and merchant-credit postings use shorter lags.

In a February order cohort of **54,000 orders**, 8,660 service tickets required a decision. On the same candidate events, 1,424 tickets had a true rule or end-state defect. A bot-completed signal plus a successful acknowledgement passed 1,360 defective tickets. Independent verification flagged **1,302 of 1,424** (91.43%); 122 defective tickets lacked sufficient evidence for a verdict. No correct ticket received a verifier FAIL. This result depends on aligned rules and trustworthy identifiers; some correct tickets remained inconclusive.

**Operational consequence.** Review queues moved from 850 to 2,728 tickets. An evidence bundle can make an individual investigation shorter; more investigations can still cost more. Missing readback stays inconclusive after the corrected release unless the source itself is restored.

**Financial interpretation.** Gross synthetic excess postings total CNY 21,555.23 under both A and B. Neither workflow stopped a candidate payment. Only a future release gate could change later postings. Base assumptions give CNY 3,958.46 of conditional exposure opportunity and a net estimate of **CNY -37,088.18** after modeled labor and verification costs. No realized savings are observed or estimated as an accomplished result.

[Detailed matched comparison and case traces](comparison.md) · [Chart of decisions](verdicts.svg) · [Sensitivity chart](economics.svg) · [Machine-readable evidence](dashboard.json) · [Synthetic SQLite database](synthetic.sqlite)
