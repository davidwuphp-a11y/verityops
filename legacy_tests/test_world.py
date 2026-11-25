import unittest
from src.world import World, agent, violations


class Baseline(unittest.TestCase):
    def test_full_refund(self):
        world = World()
        self.addCleanup(world.db.close)
        agent(world, lambda _: ())
        self.assertEqual(world.order()["status"], "refunded")
        self.assertEqual([p["amount"] for p in world.ledger()], [10000])
        self.assertEqual(violations(world.order(), world.ledger()), [])

