# VerityOps

VerityOps checks the business outcome of a simulated full-refund workflow. The demo includes a case where every write tool reports success, the payment ledger contains the expected refund, and the order is marked refunded. A fresh read of the ticket still shows it open. The contract returns **FAIL** and saves a replayable regression.

Run from the repository root with Python 3.11 or later and SQLite support:

```sh
python -B -m verityops
```

The first output line names a new evidence directory. The default batch exercises eleven deterministic scenarios: **4 PASS, 6 FAIL and 1 INCONCLUSIVE**. Exit zero means the batch matched its expected labels, including the planted failures. No accounts, models, payment credentials or production connections are needed.

| Question | Where to look |
|---|---|
| How do I reproduce a failure and retest the reference release? | [Quickstart](QUICKSTART.md) |
| What counts as an authoritative observation? | [Architecture](ARCHITECTURE.md) and [decision rules](TECHNICAL_DESIGN.md) |
| Which checks have actually been run? | [Testing](TESTING.md) and [machine-readable results](test-results.json) |
| What remains unverified outside the fixture? | [Limitations](LIMITATIONS.md) and [read-only preflight](READBACK_PREFLIGHT.md) |
| How do I install, contribute or raise a security concern? | [Installation](INSTALLATION.md), [contribution guide](CONTRIBUTING.md), [security](SECURITY.md) |

This source release uses synthetic SQLite records. A customer integration, external ledger completeness and live release sign-off would need separate evidence. Project-owned release materials use the [Apache License 2.0](LICENSE). Dependency and component provenance is recorded in [DEPENDENCIES.md](DEPENDENCIES.md).
