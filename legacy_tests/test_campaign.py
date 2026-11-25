import unittest
from src.campaign import minimize, run, schedules


class Campaign(unittest.TestCase):
    def test_witnesses(self):
        for op, stage, issue in [
            ("cancel","checked","cancelled_at_commit"), ("expire","checked","expired_at_commit"),
            ("withdraw","checked","missing_approved"), ("revoke","checked","missing_permitted"),
            ("compete","checked","duplicate"), ("redeliver","committed","duplicate"),
            ("lose_reply","committed","duplicate"), ("drop_sync","project","projection_mismatch"),
        ]:
            with self.subTest(op=op):
                plan = [[op, stage]]
                self.assertIn(issue, run(plan)["issues"])
                self.assertEqual([], run(plan, guarded=True)["issues"])

    def test_timing_matters(self):
        self.assertEqual([], run([["revoke", "start"]])["ledger"])
        self.assertEqual([], run([["revoke", "end"]])["issues"])
        self.assertEqual("invalid", run([["revoke","start"],["lose_reply","committed"]])["status"])
        self.assertEqual("equivalent", run([["cancel","end"]])["status"])

    def test_reduction(self):
        plan = [["lose_reply","committed"],["expire","end"]]
        self.assertEqual(plan[:1], minimize(plan, run(plan)["issues"]))

    def test_incomplete_observation(self):
        result = run([["lose_reply", "committed"]], observe_payments=False)
        self.assertEqual("unobservable", result["status"])
        self.assertIsNone(result["issues"])

    def test_equal_operator_budgets(self):
        for groups in schedules(0, 100):
            self.assertEqual([op for op, _ in groups["B"]], [op for op, _ in groups["C"]])

