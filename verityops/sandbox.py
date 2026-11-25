"""Deterministic driver plus replaceable action adapter in a disposable SQLite fixture."""
from contextlib import closing
from pathlib import Path
from typing import Protocol
import sqlite3
from .fixture.world import World
from .contract import Task, snapshot
from .observer import observe


class ActionAdapter(Protocol):
    def __call__(self, tools, task: Task) -> str: ...


class Tools:
    def __init__(self, world, release, stimulus):
        self.world = world
        self.release = release
        self.stimulus = stimulus
        self.trace = []
        self.attempt = 0

    def event(self, operation, request, response):
        self.trace.append(dict(attempt=self.attempt, operation=operation, request=request, response=response))
        return response

    def inspect(self):
        return self.event("read", {}, self.world.order())

    def refund(self, task):
        w = self.world
        if self.stimulus == "withdraw_before_commit":
            w.db.execute("UPDATE orders SET permitted=0 WHERE order_id=?", (w.order_id,))
        if not w.order()["permitted"] and self.release != "stale_policy":
            return self.event("refund", {"cents": task.amount_cents}, "denied")
        if self.release != "ack_only":
            key = task.order if self.release != "unstable_retry" else f"{task.order}-{self.attempt}"
            cents = task.amount_cents - int(self.release == "short_post")
            w.refund(key, cents, "sandbox-agent")
        return self.event("refund", {"cents": task.amount_cents}, "ok")

    def project(self):
        if self.release == "sync_error":
            return self.event("sync", {}, "error")
        if self.release != "ack_only":
            self.world.db.execute("UPDATE orders SET status='refunded' WHERE order_id=?", (self.world.order_id,))
        return self.event("sync", {}, "ok")

    def close_ticket(self):
        if self.release not in {"ack_only", "open_case"}:
            self.world.db.execute("UPDATE tickets SET status='closed' WHERE order_ref=?", (self.world.order_id,))
        return self.event("close", {}, "ok")


def controller(tools, task):
    order = tools.inspect()
    if order["status"] == "refunded" and tools.release != "unstable_retry":
        return "completed"
    if not order["approved"] or not order["permitted"]:
        return "held"
    if tools.refund(task) == "denied":
        return "held"
    if tools.project() == "error":
        return "incomplete"
    tools.close_ticket()
    return "completed"


def execute(path: Path, task, stimulus, release, adapter: ActionAdapter = controller):
    # Each run owns a new file; path creation is exclusive even across processes.
    with path.open("xb"):
        pass
    world = World(task.order)
    with closing(world.db) as fixture_db, closing(sqlite3.connect(path, isolation_level=None)) as db:
        fixture_db.backup(db)
        world.db = db
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE TABLE tickets(order_ref TEXT PRIMARY KEY NOT NULL REFERENCES orders(order_id), status TEXT)")
        db.execute("INSERT INTO tickets VALUES (?, 'open')", (task.order,))
        db.execute("UPDATE orders SET paid=?, approved=? WHERE order_id=?", (task.amount_cents, int(stimulus != "unapproved"), task.order))
        tools = Tools(world, release, stimulus)

        def read(phase):
            if phase == "after" and stimulus == "blind_ledger":
                return {"unavailable": "refund source withheld by fixture"}
            return snapshot(path, task.order)

        def invoke(attempt, current):
            tools.attempt = attempt
            return adapter(tools, current)

        result = observe(task, read, invoke, deliveries=2 if stimulus == "redelivery" else 1)
        return {**result, "trace": tools.trace}
