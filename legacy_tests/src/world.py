"""Local refund tool API. Amounts are integer cents. One order, one full refund."""
import sqlite3


class World:
    def __init__(self):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE orders(status TEXT, paid INTEGER, approved INTEGER,
                                permitted INTEGER, clock INTEGER, deadline INTEGER);
            INSERT INTO orders VALUES ('paid', 10000, 1, 1, 0, 10);
            CREATE TABLE payments(id INTEGER PRIMARY KEY, request_key TEXT UNIQUE,
                amount INTEGER, actor TEXT, approved INTEGER, permitted INTEGER,
                status TEXT, clock INTEGER, deadline INTEGER);
        """)
        self.trace = []

    def order(self):
        return dict(self.db.execute("SELECT * FROM orders").fetchone())

    def ledger(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM payments ORDER BY id")]

    def refund(self, key, amount, actor):
        # Provider deduplicates by caller-supplied key. Audit fields sample live truth.
        self.db.execute("""
            INSERT OR IGNORE INTO payments(request_key, amount, actor, approved,
                permitted, status, clock, deadline)
            SELECT ?, ?, ?, approved, permitted, status, clock, deadline FROM orders
        """, (key, amount, actor))


def eligible(order):
    return (order["status"] == "paid" and order["approved"] and order["permitted"]
            and order["clock"] < order["deadline"])


def agent(world, hook, actor="primary", guarded=False):
    hook("start")
    snapshot = world.order()
    world.trace.append(["read", actor, snapshot])
    if not eligible(snapshot):
        return
    hook("checked")
    if guarded and not eligible(world.order()):
        return
    key = "order-1" if guarded else f"{actor}-1"
    world.refund(key, snapshot["paid"], actor)
    world.trace.append(["payment", actor, key])
    if "lose_reply" in hook("committed"):
        retry_key = key if guarded else f"{actor}-2"
        world.refund(retry_key, snapshot["paid"], actor)
        world.trace.append(["retry", actor, retry_key])
    dropped = "drop_sync" in hook("project")
    if guarded or not dropped:
        world.db.execute("UPDATE orders SET status='refunded'")
        world.trace.append(["project", actor])


def violations(order, payments):
    issues = set()
    if len(payments) > 1:
        issues.add("duplicate")
    if sum(p["amount"] for p in payments) > order["paid"]:
        issues.add("overpaid")
    for payment in payments:
        for field in ("approved", "permitted"):
            if not payment[field]:
                issues.add("missing_" + field)
        if payment["status"] == "cancelled":
            issues.add("cancelled_at_commit")
        if payment["clock"] >= payment["deadline"]:
            issues.add("expired_at_commit")
    if bool(payments) != (order["status"] == "refunded"):
        issues.add("projection_mismatch")
    return sorted(issues)

