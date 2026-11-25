"""Public reproduction of the frozen synthetic missing-row exercise."""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from verityops.contract import Task
from verityops.sandbox import execute


class ReadbackCompleteness(unittest.TestCase):
    def test_consistent_view_count_can_hide_second_refund(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.db"
            evidence = execute(path, Task(), "redelivery", "unstable_retry")
            self.assertEqual(evidence["decision"]["verdict"], "FAIL")
            with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
                db.execute("BEGIN")
                db.execute("CREATE TEMP VIEW limited AS SELECT * FROM payments WHERE id=(SELECT min(id) FROM payments)")
                witness = db.execute("SELECT id FROM payments WHERE order_id=? ORDER BY id", ("order-1",)).fetchall()
                visible = db.execute("SELECT id FROM limited WHERE order_id=? ORDER BY id", ("order-1",)).fetchall()
                count = db.execute("SELECT count(*) FROM limited WHERE order_id=?", ("order-1",)).fetchone()[0]
                self.assertEqual(len(visible), count)
                self.assertEqual((witness, visible), ([(1,), (2,)], [(1,)]))
