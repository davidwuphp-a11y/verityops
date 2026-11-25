"""Deterministic schedules at tool boundaries. No network, threads or model calls."""
import random
from .world import World, agent, violations

STAGES = ("start", "checked", "committed", "project", "end")
# Legal injection sites. Both generators draw from this same candidate space.
SITES = {
    "cancel": STAGES, "expire": STAGES, "withdraw": STAGES, "revoke": STAGES,
    "compete": STAGES, "redeliver": ("committed", "end"),
    "lose_reply": ("committed",), "drop_sync": ("project",),
}
STATE_CHANGES = {
    "cancel": "UPDATE orders SET status='cancelled' WHERE status='paid' AND NOT EXISTS (SELECT 1 FROM payments)",
    "expire": "UPDATE orders SET clock=deadline WHERE clock<deadline",
    "withdraw": "UPDATE orders SET approved=0 WHERE approved=1",
    "revoke": "UPDATE orders SET permitted=0 WHERE permitted=1",
}
# For guards sampled at read, target the read/commit interval. For duplicate
# deliveries target a committed effect whose projection is still pending.
WINDOW = {op: "checked" for op in (*STATE_CHANGES, "compete")}
WINDOW["redeliver"] = "committed"


def schedules(seed, budget):
    rng = random.Random(seed)
    placement = random.Random(seed + 100000)
    for _ in range(budget):
        operators = rng.sample(list(SITES), rng.choice((1, 2)))
        random_plan = [[op, placement.choice(SITES[op])] for op in operators]
        guided = [[op, WINDOW.get(op, SITES[op][0])] for op in operators]
        yield {"A": [], "B": random_plan, "C": guided}


def run(plan, guarded=False, observe_payments=True):
    world = World()
    seen = []
    changed = []
    try:
        def hook(stage):
            signals = []
            for index, (op, target) in enumerate(plan):
                if stage != target or stage not in SITES.get(op, ()):
                    continue
                seen.append(index)
                world.trace.append(["inject", op, stage])
                if op in STATE_CHANGES:
                    if world.db.execute(STATE_CHANGES[op]).rowcount:
                        changed.append(index)
                elif op in ("compete", "redeliver"):
                    other = "worker-2" if op == "compete" else "delivery-2"
                    agent(world, lambda _: (), other, guarded)
                    changed.append(index)
                else:
                    signals.append(op)
                    changed.append(index)
            return signals

        agent(world, hook, guarded=guarded)
        hook("end")
        order = world.order()
        ledger = world.ledger() if observe_payments else None
        issues = violations(order, ledger) if ledger is not None else None
        if len(seen) != len(plan):
            status = "invalid"
        elif ledger is None:
            status = "unobservable"
        elif not plan:
            status = "original"
        elif not changed:
            status = "equivalent"
        elif issues:
            status = "detected"
        else:
            status = "survived"
        return dict(plan=plan, seen=seen, changed=changed, status=status,
                    issues=issues, order=order, ledger=ledger, trace=world.trace)
    finally:
        world.db.close()


def minimize(plan, signature):
    """One-deletion minimal for this exact oracle signature."""
    current = list(plan)
    index = 0
    while index < len(current):
        trial = current[:index] + current[index + 1:]
        outcome = run(trial)
        if outcome["status"] == "detected" and outcome["issues"] == signature:
            current = trial
            index = 0
        else:
            index += 1
    return current

