"""Hand-labelled expectations for every legal single injection in this fixture."""
import unittest
from src.campaign import SITES, run


class Reference(unittest.TestCase):
    def test_all_single_faults(self):
        duplicates = ["duplicate", "overpaid"]
        expected = {
            ("cancel", "checked"): ["cancelled_at_commit"],
            ("expire", "checked"): ["expired_at_commit"],
            ("withdraw", "checked"): ["missing_approved"],
            ("revoke", "checked"): ["missing_permitted"],
            ("compete", "checked"): duplicates,
            ("compete", "committed"): duplicates,
            ("compete", "project"): duplicates,
            ("redeliver", "committed"): duplicates,
            ("lose_reply", "committed"): duplicates,
            ("drop_sync", "project"): ["projection_mismatch"],
        }
        for op, stages in SITES.items():
            for stage in stages:
                with self.subTest(op=op, stage=stage):
                    self.assertEqual(expected.get((op, stage), []), run([[op, stage]])["issues"])

