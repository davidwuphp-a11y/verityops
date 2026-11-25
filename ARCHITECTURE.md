# Architecture

One run creates an isolated SQLite database with a paid order, an open ticket and an empty refund ledger. The task specifies the expected disposition and integer amount. The deterministic controller exercises the configured release through the tool adapter.

| Component | Responsibility |
|---|---|
| `verityops/fixture/world.py`, `sandbox.py` | Create resources and simulate execution. A posted refund records its order's primary key, amount and policy state at submission. Write calls can exhibit the selected fault. |
| `observer.py` | Call an independently supplied reader before execution; invoke the actor only for a supported start; read again after execution, including after a caught action exception. |
| `contract.py` | Open a new SQLite connection with URI `mode=ro` and start a read transaction for each snapshot. Validate structure, ownership, row counts, policy and projections. |
| `run.py` | Run scenarios, compare observed labels, save evidence, create regressions for failures, and replay the defective and reference variants in fresh databases. |
| `baselines.py` | Compare reply-only, trace-based and hand-written state assertions. An optional comparison uses a separately installed third-party framework. |

The judge receives the task and snapshots. Replies and trace entries accompany the decision for diagnosis. The expected scenario label is used by the batch harness after the decision. Read-only SQLite connections provide a local separation between observation and action. In a live system, independent identities, trustworthy records and a signed-off observation window would also be needed.
