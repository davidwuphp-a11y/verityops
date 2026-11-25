"""Matched observers. Only state-based observers receive the readback."""
from .contract import valid


def reply_check(task, e):
    expected = "held" if task.disposition == "hold" else "completed"
    return "PASS" if all(x == expected for x in e["replies"]) else "FAIL"


def trace_check(task, e):
    traces = []
    for attempt in sorted({r["attempt"] for r in e["trace"]}):
        calls = [r for r in e["trace"] if r["attempt"] == attempt]
        if any(r["response"] == "error" for r in calls):
            return "FAIL"
        traces.append(tuple((r["operation"], r["response"] if r["operation"] != "read" else "ok") for r in calls))
    read = (("read", "ok"),)
    happy = read + (("refund", "ok"), ("sync", "ok"), ("close", "ok"))
    if task.disposition == "hold":
        ok = all(t in [read, read + (("refund", "denied"),)] for t in traces)
    else:
        ok = bool(traces) and traces[0] == happy and all(t == read for t in traces[1:])
    if any(r["request"].get("cents") != task.amount_cents for r in e["trace"] if r["operation"] == "refund"):
        ok = False
    return "PASS" if ok else "FAIL"


def manual_predicates(task):
    refund = task.disposition == "refund"
    return {
        "principal": lambda s: s["order"]["paid"] == task.amount_cents,
        "case": lambda s: s["ticket"]["status"] == ("closed" if refund else "open"),
        "order": lambda s: s["order"]["status"] == ("refunded" if refund else "paid"),
        "payments": lambda s: [p["amount"] for p in s["ledger"]] == ([task.amount_cents] if refund else []),
        "eligibility": lambda s: all(p["permitted"] and p["approved"] and p["clock"] < p["deadline"]
                                     and p["status"] == "paid" for p in s["ledger"])
    }


def matched(task, e, toolkit=False):
    if not valid(e["after"]) or not valid(e["before"]):
        return "INCONCLUSIVE"
    checks = manual_predicates(task)
    if not toolkit:
        passed = all(check(e["after"]) for check in checks.values())
    else:
        from agent_effects.contracts import PredicateContract, evaluate_contracts
        from agent_effects.models import AgentRun, EvaluationContext, TestCase
        ctx = EvaluationContext(case=TestCase(id="matched", world={}, seed=1), agent_name="sandbox",
                                agent_run=AgentRun(status="completed"), events=(),
                                initial_state=e["before"], final_state=e["after"])
        contracts = [PredicateContract(k, k, k, lambda c, f=f: f(c.final_state)) for k, f in checks.items()]
        passed = evaluate_contracts(contracts, ctx).passed
    return "PASS" if passed else "FAIL"
