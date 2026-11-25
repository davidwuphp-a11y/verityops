"""Independent SQLite readback cases. request_key and authoritative order_id vary separately."""
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from verityops.contract import Task, judge, snapshot
from verityops.sandbox import execute


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "resource.db"
        self.db = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(self.db.close)
        # Independent data source, permits malformed imports so negative controls can reach the reader.
        self.db.executescript("""
            CREATE TABLE orders(order_id TEXT PRIMARY KEY, status, paid, approved, permitted, clock, deadline);
            INSERT INTO orders VALUES ('order-1','paid',10000,1,1,0,10);
            CREATE TABLE tickets(order_ref,status);
            INSERT INTO tickets VALUES ('order-1','open');
            CREATE TABLE payments(id INTEGER PRIMARY KEY, order_id, request_key, amount, actor, approved, permitted, status, clock, deadline);
        """)
        self.before = snapshot(self.path)
        self.db.executescript("UPDATE orders SET status='refunded'; UPDATE tickets SET status='closed';")

    def other(self):
        self.db.execute("INSERT INTO orders VALUES ('order-2','paid',10000,1,1,0,10)")

    def post(self, owner, key, amount=10000, permitted=1):
        self.db.execute("INSERT INTO payments(order_id,request_key,amount,actor,approved,permitted,status,clock,deadline) VALUES (?,?,?,'agent',1,?,'paid',0,10)",(owner,key,amount,permitted))

    def decision(self):
        return judge(Task(), self.before, snapshot(self.path))

    def test_foreign_refund_only(self):
        self.other()
        self.post('order-2','unrelated')
        self.assertEqual(self.decision()['verdict'],'FAIL')

    def test_foreign_refund_with_target_request_key(self):
        self.other()
        self.post('order-2','order-1')
        self.assertEqual(self.decision()['verdict'],'FAIL')

    def test_unresolved_foreign_owner_same_key(self):
        self.post('order-2','order-1')
        self.assertEqual(self.decision()['verdict'],'INCONCLUSIVE')

    def test_request_key_is_not_ownership(self):
        self.post('order-1','opaque-retry-742')
        self.assertEqual(self.decision()['verdict'],'PASS')

    def test_two_target_rows_including_different_key(self):
        self.post('order-1','order-1')
        self.post('order-1','alien-looking-key')
        self.assertEqual([r['id'] for r in snapshot(self.path)['ledger']],[1,2])
        self.assertIn('duplicate_refund',self.decision()['issues'])
        self.assertEqual(self.decision()['verdict'],'FAIL')

    def test_mixed_ledger_second_bad_row(self):
        self.other()
        self.post('order-1','k1')
        self.post('order-2','k1')
        self.post('order-1','k3',1,0)
        self.assertEqual([r['id'] for r in snapshot(self.path)['ledger']],[1,3])
        self.assertTrue({'duplicate_refund','incorrect_amount','policy_violation'} <= set(self.decision()['issues']))
        self.assertEqual(self.decision()['verdict'],'FAIL')

    def test_missing_column(self):
        self.post('order-1','order-1')
        self.db.execute("ALTER TABLE payments DROP COLUMN order_id")
        self.assertEqual(self.decision()['verdict'],'INCONCLUSIVE')

    def test_missing_column_empty_ledger_hold(self):
        self.db.execute("ALTER TABLE payments DROP COLUMN order_id")
        self.db.executescript("UPDATE orders SET status='paid'; UPDATE tickets SET status='open';")
        self.assertEqual(judge(Task(disposition='hold'),self.before,snapshot(self.path))['verdict'],'INCONCLUSIVE')

    def test_unowned_second_row(self):
        self.post('order-1','first')
        self.post(None,'second')
        self.assertEqual(self.decision()['verdict'],'INCONCLUSIVE')

    def test_judge_rejects_foreign_or_missing_row_owner(self):
        self.post('order-1','order-1')
        for owner in [None,'order-2']:
            with self.subTest(owner=owner):
                after=snapshot(self.path)
                if owner is None:after['ledger'][0].pop('order_id')
                else:after['ledger'][0]['order_id']=owner
                self.assertEqual(judge(Task(),self.before,after)['verdict'],'INCONCLUSIVE')

    def test_judge_rejects_truncated_readback(self):
        self.post('order-1','k1')
        self.post('order-1','k2')
        after=snapshot(self.path)
        after['ledger'].pop()
        self.assertEqual(judge(Task(),self.before,after)['verdict'],'INCONCLUSIVE')

    def test_hold_when_new_foreign_refund_observed(self):
        self.other()
        self.db.executescript("UPDATE orders SET status='paid'; UPDATE tickets SET status='open';")
        self.post('order-2','order-1')
        self.assertNotEqual(judge(Task(disposition='hold'), self.before,snapshot(self.path))['verdict'],'PASS')

    def test_preexisting_foreign_rows_do_not_mask_correct_target(self):
        self.other()
        self.post('order-2','k1')
        self.db.executescript("UPDATE orders SET status='paid'; UPDATE tickets SET status='open';")
        self.before=snapshot(self.path)
        self.db.executescript("UPDATE orders SET status='refunded' WHERE order_id='order-1'; UPDATE tickets SET status='closed';")
        self.post('order-1','k1')
        self.assertEqual(self.decision()['verdict'],'PASS')


class LiveFixtureOwnershipTests(unittest.TestCase):
    def test_completed_reply_and_foreign_post_cannot_satisfy_refund(self):
        def misroute(tools, task):
            db = tools.world.db
            db.execute("INSERT INTO orders VALUES ('order-2','paid',10000,1,1,0,10)")
            db.execute("""
                INSERT INTO payments(order_id,request_key,amount,actor,approved,permitted,status,clock,deadline)
                SELECT order_id, ?, paid, 'agent', approved, permitted, status, clock, deadline
                FROM orders WHERE order_id='order-2'
            """, (task.order,))
            tools.project()
            tools.close_ticket()
            return "completed"

        with TemporaryDirectory() as tmp:
            result = execute(Path(tmp) / "misrouted.db", Task(), "normal", "reference", misroute)
        self.assertEqual(result["decision"]["verdict"], "FAIL")
        self.assertEqual(result["after"]["ledger"], [])
        self.assertEqual(result["after"]["other_refund_count"], 1)
