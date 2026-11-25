import json
from pathlib import Path
from contextlib import closing
import sqlite3
import unittest
from tempfile import TemporaryDirectory
from verityops.contract import Task, judge, snapshot
from verityops.run import ROOT, replay
from verityops.sandbox import execute
from verityops.observer import observe

class OutcomeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "fixture.db"

    def test_all_fixtures(self):
        for c in json.loads((ROOT / "scenarios.json").read_text()):
            with self.subTest(c["id"]):
                e = execute(self.path.with_name(c["id"]+".db"), Task(disposition=c["disposition"]),
                            c["stimulus"], c["release"])
                self.assertEqual(e["decision"]["verdict"], c["gold"])

    def test_reader_reports_missing_without_creating_file(self):
        self.assertIn("unavailable", snapshot(self.path))
        self.assertFalse(self.path.exists())

    def test_capture_matches_persisted_rows(self):
        e = execute(self.path, Task(), "normal", "short_post")
        self.assertEqual(snapshot(self.path), e["after"])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT amount FROM payments").fetchone()[0], 9999)

    def test_malformed_and_initial_readback(self):
        e = execute(self.path, Task(), "normal", "reference")
        for b,a in [({}, e["after"]), (e["after"], e["after"]), (e["before"], {"schema":"single-refund/1"}),
                    (e["before"], {**e["after"], "ledger":[{}]})]:
            self.assertEqual(judge(Task(), b, a)["verdict"], "INCONCLUSIVE")

    def test_no_fixture_overwrite(self):
        self.path.write_bytes(b"prior")
        with self.assertRaises(FileExistsError):
            execute(self.path, Task(), "normal", "reference")
        self.assertEqual(self.path.read_bytes(), b"prior")

    def test_distinct_amount_and_repeat(self):
        spec = dict(format="refund-regression/1", task=dict(amount_cents=2193), stimulus="redelivery")
        for release, expected in [("unstable_retry","FAIL"), ("reference","PASS")]:
            self.assertEqual(replay(spec, release, self.path.with_name(release+".db"))["decision"]["verdict"], expected)

    def test_reply_cannot_manufacture_effect(self):
        e = execute(self.path, Task(), "normal", "reference", lambda tools, task:"completed")
        self.assertEqual(e["decision"]["outcome"], "no_effect")

    def test_unavailable_before_invoking(self):
        calls = []
        def down(phase):
            raise TimeoutError()
        e = observe(Task(), down, lambda *args: calls.append(args))
        self.assertEqual(e["decision"]["verdict"], "INCONCLUSIVE")
        self.assertEqual(calls, [])

    def test_exception_after_payment_reads_resource(self):
        def interrupted(tools, task):
            tools.refund(task)
            raise ConnectionError()
        e = execute(self.path, Task(), "normal", "reference", interrupted)
        self.assertEqual(e["decision"]["outcome"], "partial")
        self.assertEqual(e["replies"], ["execution_error:ConnectionError"])
