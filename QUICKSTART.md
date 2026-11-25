# Reproduce an incorrect refund outcome

Use the repository root for these commands so the example paths resolve. The core demonstration is offline.

```sh
python -B -m verityops
python -B -m verityops --replay examples/open_ticket.json --release open_case
python -B -m verityops --replay examples/open_ticket.json --release reference
python -B -m verityops --replay examples/blind_ledger.json --release reference
```

| Invocation | Expected observation | Exit |
|---|---|---:|
| Batch | 11 matching labels; six failures reproduced exactly and all six reference runs pass | 0 |
| Open ticket, defective release | FAIL, partial, issue `case_projection` | 1 |
| Same input, reference release | PASS, completed | 0 |
| Reference with ledger withheld | INCONCLUSIVE, unavailable_readback | 2 |

Each invocation prints a different run directory. Open `open_ticket/evidence.json` inside the batch directory. Compare `replies` and `trace` with `after.ledger`, `after.order.status` and `after.ticket.status`. Expect one refund for 10000 minor units, a refunded order and an open ticket. The case directory includes the SQLite resource, generated replay specification and separate original/reference evidence. For single replays, the evidence file is at the root of the printed run directory. Use the single-case exit codes deliberately when scripting; the defective example is expected to exit nonzero.
