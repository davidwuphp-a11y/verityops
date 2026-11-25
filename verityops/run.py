"""Offline demo, matched observers and executable regression replay."""
import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import json
import platform
from pathlib import Path
import sqlite3
import sys
from time import perf_counter
from uuid import uuid4
from .contract import Task
from .sandbox import execute
from .baselines import matched, reply_check, trace_check

ROOT = Path(__file__).resolve().parent
RELEASES = {"reference", "ack_only", "short_post", "unstable_retry", "open_case", "stale_policy", "sync_error"}
STIMULI = {"normal", "redelivery", "unapproved", "withdraw_before_commit", "blind_ledger"}


def save(path, data):
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def new_run():
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    path = Path.cwd() / "runs" / (now + "_" + uuid4().hex[:8])
    path.mkdir(parents=True)
    return path


def replay(spec, release, dest):
    if spec.get("format") != "refund-regression/1" or spec["stimulus"] not in STIMULI or release not in RELEASES:
        raise ValueError("unsupported regression or release")
    return execute(dest, Task(**spec["task"]), spec["stimulus"], release)


def batch(path, toolkit):
    cases = json.loads((ROOT / "scenarios.json").read_text())
    results = []
    for c in cases:
        d = path / c["id"]
        d.mkdir()
        task = Task(disposition=c["disposition"])
        started = perf_counter()
        e = execute(d / "resource.db", task, c["stimulus"], c["release"])
        save(d / "evidence.json", e)
        verdicts = dict(reply=reply_check(task, e), trace=trace_check(task, e),
                        manual=matched(task, e), engine=e["decision"]["verdict"])
        if toolkit:
            verdicts["effects_testkit"] = matched(task, e, True)
        row = dict(case=c["id"], gold=c["gold"], verdicts=verdicts, outcome=e["decision"]["outcome"],
                   issues=e["decision"]["issues"], elapsed_seconds=perf_counter()-started)
        if verdicts["engine"] == "FAIL":
            spec = dict(format="refund-regression/1", task=asdict(task), stimulus=c["stimulus"],
                        observed_release=c["release"], required_verdict="PASS")
            save(d / "regression.json", spec)
            for label, release in [("original", c["release"]), ("reference", "reference")]:
                again = replay(spec, release, d / (label + ".db"))
                save(d / (label + ".json"), again)
                row[label] = again["decision"]["verdict"]
                if label == "original":
                    row["exact_replay"] = again == e
        results.append(row)
    summary = dict(cases=results, interpreter=sys.version, sqlite=sqlite3.sqlite_version,
                   platform=platform.platform(), toolkit=toolkit,
                   counts={k:dict(Counter(r["verdicts"][k] for r in results)) for k in results[0]["verdicts"]})
    save(path / "results.json", summary)
    return all(r["gold"] == r["verdicts"]["engine"] and
               (r["gold"] != "FAIL" or (r["exact_replay"] and r["reference"] == "PASS")) for r in results)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--testkit", action="store_true", help="include the separately installed Agent Effects Testkit comparison")
    p.add_argument("--replay", type=Path)
    p.add_argument("--release", choices=sorted(RELEASES))
    a = p.parse_args()
    if bool(a.replay) != bool(a.release):
        p.error("provide --replay and --release together")
    out = new_run()
    print(out, flush=True)
    if a.replay:
        spec = json.loads(a.replay.read_text(encoding="utf8"))
        result = replay(spec, a.release, out / "resource.db")
        save(out / "evidence.json", result)
        print(json.dumps(result["decision"]))
        return {"PASS":0, "FAIL":1, "INCONCLUSIVE":2}[result["decision"]["verdict"]]
    good = batch(out, a.testkit)
    print((out/"results.json").read_text())
    return int(not good)


if __name__ == "__main__":
    sys.exit(main())
