"""Outcome oracle for an isolated single-order, full-refund task."""
from dataclasses import dataclass, asdict
import sqlite3
from pathlib import Path
from contextlib import closing

SCHEMA = "single-refund/2"

@dataclass(frozen=True)
class Task:
    order: str = "order-1"
    amount_cents: int = 10000
    disposition: str = "refund"

    def __post_init__(self):
        if self.order != "order-1" or type(self.amount_cents) is not int or self.amount_cents <= 0:
            raise ValueError("Only a single isolated positive-amount order is supported")
        if self.disposition not in {"refund", "hold"}:
            raise ValueError("Invalid disposition")


def snapshot(path: Path, order_id="order-1"):
    """One read transaction; an unavailable/incompatible resource cannot yield PASS."""
    try:
        with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
            db.row_factory = sqlite3.Row
            db.execute("BEGIN")
            orders = db.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchall()
            tickets = db.execute("SELECT * FROM tickets WHERE order_ref=?", (order_id,)).fetchall()
            if len(orders) != 1 or len(tickets) != 1:
                raise ValueError("Expected one scoped order and one ticket")
            # Check the entire authorized fixture partition before filtering: an
            # unassigned or dangling refund might be the target's second posting.
            unresolved = db.execute("""
                SELECT 1 FROM payments AS p LEFT JOIN orders AS o ON o.order_id=p.order_id
                WHERE typeof(p.order_id)!='text' OR trim(p.order_id)='' OR o.order_id IS NULL
                LIMIT 1
            """).fetchone()
            if unresolved:
                raise ValueError("Unresolved refund order_id in the evidence partition")
            total, matched = db.execute(
                "SELECT count(*), count(CASE WHEN order_id=? THEN 1 END) FROM payments", (order_id,)
            ).fetchone()
            rows = [dict(r) for r in db.execute(
                "SELECT * FROM payments WHERE order_id=? ORDER BY id", (order_id,)
            )]
            return dict(schema=SCHEMA, order=dict(orders[0]), ticket=dict(tickets[0]), ledger=rows,
                        target_refund_count=matched, other_refund_count=total-matched)
    except (sqlite3.Error, ValueError, OSError) as exc:
        return {"unavailable": str(exc)}


def valid(s, order_id="order-1"):
    if not isinstance(s, dict) or s.get("schema") != SCHEMA:
        return False
    try:
        o, t, rows = s["order"], s["ticket"], s["ledger"]
        def flags(r):
            return all(type(r[k]) is int and r[k] in (0, 1) for k in ("approved", "permitted"))
        def times(r):
            return all(type(r[k]) is int for k in ("clock", "deadline"))
        return (o["order_id"] == order_id and o["status"] in ("paid", "refunded") and type(o["paid"]) is int
                and flags(o) and times(o) and t["order_ref"] == order_id
                and t["status"] in ("open", "closed") and isinstance(rows, list)
                and type(s["target_refund_count"]) is int and s["target_refund_count"] == len(rows)
                and type(s["other_refund_count"]) is int and s["other_refund_count"] >= 0
                and all(r["order_id"] == o["order_id"] and type(r["id"]) is int and type(r["amount"]) is int and
                        isinstance(r["request_key"], str) and isinstance(r["actor"], str)
                        and isinstance(r["status"], str) and flags(r) and times(r) for r in rows)
                and len({r["id"] for r in rows}) == len(rows))
    except (TypeError, KeyError):
        return False


def supported_start(task, before):
    return (valid(before, task.order) and not before["ledger"] and before["order"]["status"] == "paid"
            and before["ticket"]["status"] == "open" and before["order"]["paid"] == task.amount_cents)


def judge(task, before, after):
    def result(verdict, outcome, issues):
        return dict(verdict=verdict, outcome=outcome, issues=issues, contract=asdict(task))
    if not valid(before, task.order) or not valid(after, task.order):
        return result("INCONCLUSIVE", "unavailable_readback", ["missing or incompatible resource evidence"])
    if not supported_start(task, before):
        return result("INCONCLUSIVE", "unsupported_start", ["fixture does not match agreed starting state"])
    rows, o, t = after["ledger"], after["order"], after["ticket"]
    hold = task.disposition == "hold"
    errors = []
    if before["order"]["paid"] != o["paid"]:
        errors.append("paid_principal_changed")
    if len(rows) > 1:
        errors.append("duplicate_refund")
    if len(rows) != int(not hold):
        errors.append("ledger_cardinality")
    if any(r["amount"] != task.amount_cents for r in rows):
        errors.append("incorrect_amount")
    if any(not r["approved"] or not r["permitted"] or r["clock"] >= r["deadline"]
           or r["status"] != "paid" for r in rows) or (hold and rows):
        errors.append("policy_violation")
    if o["status"] != ("paid" if hold else "refunded"):
        errors.append("order_projection")
    if t["status"] != ("open" if hold else "closed"):
        errors.append("case_projection")
    if not errors:
        if before["other_refund_count"] != after["other_refund_count"]:
            return result("INCONCLUSIVE", "unexpected_partition_activity", ["other_order_refund_count_changed"])
        return result("PASS", "correct_hold" if hold else "completed", [])
    effects = (bool(rows), o["status"] == "refunded", t["status"] == "closed")
    if "duplicate_refund" in errors:
        outcome = "duplicate"
    elif not any(effects):
        outcome = "no_effect"
    elif not all(effects):
        outcome = "partial"
    else:
        outcome = "inconsistent"
    return result("FAIL", outcome, errors)
