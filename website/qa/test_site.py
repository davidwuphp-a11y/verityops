"""Static export and evidence checks. No network or third-party dependencies."""
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ROUTES = {"index","how-it-works","platform","research","about","contact","testing","use-cases"}

class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
    def attrs(self, tag):
        return [a for t,a in self.tags if t==tag]

class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.out = Path(cls.temp.name)
        subprocess.run([sys.executable,"-B",str(ROOT/"build.py"),"--output",str(cls.out),"--base-url","https://example.invalid/preview/"],check=True)
        cls.text={p.stem:p.read_text(encoding="utf-8") for p in cls.out.glob("*.html")}
        cls.pages={k:Page(v) for k,v in cls.text.items()}

    def test_routes_and_metadata(self):
        self.assertEqual(set(self.pages),ROUTES)
        titles = set()
        for name,page in self.pages.items():
            titles.add(self.text[name].split("<title>")[1].split("</title>")[0])
            self.assertEqual(len(page.attrs("h1")),1)
            self.assertEqual(page.attrs("html")[0]["lang"],"en")
            self.assertTrue(any(a.get("name")=="description" and a.get("content") for a in page.attrs("meta")))
            meta={a.get("property"):a.get("content") for a in page.attrs("meta")}
            self.assertEqual(meta["og:url"],f"https://example.invalid/preview/{name}.html")
            self.assertEqual(meta["og:image"],"https://example.invalid/preview/assets/social.png")
        self.assertEqual(len(titles),8)
        self.assertTrue((self.out/".nojekyll").exists())
        self.assertEqual(struct.unpack(">II",(self.out/"assets/social.png").read_bytes()[16:24]),(1200,630))

    def test_local_links_and_fragments(self):
        for name,page in self.pages.items():
            for tag,a in page.tags:
                if tag not in ("a","script","img","link") or a.get("rel")=="canonical":
                    continue
                u=urlsplit(a.get("href",a.get("src","")))
                self.assertFalse(u.netloc,u)
                self.assertFalse(u.scheme,u)
                self.assertFalse(u.path.startswith("/"),u)
                target=self.out/(u.path or name+".html")
                self.assertTrue(target.is_file(),target)
                if u.fragment:
                    self.assertIn(u.fragment,[attrs.get("id") for _,attrs in self.pages[target.stem].tags])

    def test_two_disclosures_and_task_c_counts(self):
        html=self.text["use-cases"]
        self.assertEqual(html.count("Illustrative synthetic scenario — not a real customer deployment."),2)
        for market in ("US","CN"):
            d=json.loads((self.out/f"evidence/task-c-{market}.json").read_text(encoding="utf8"))
            part=html.split(f'evidence/task-c-{market}.json')[0].rsplit('<article class="case-card">',1)[1]
            for key in ("orders","tickets"):
                self.assertIn(f'{d["counts"][key]:,}',part)
            for method in ("baseline","verified"):
                truth=d["confusion"]["candidate"][method]["defective"]
                self.assertIn("".join(f"<td>{truth[v]:,}</td>" for v in ("PASS","FAIL","INCONCLUSIVE")),part)
            self.assertIn("Financial interpretation.",part)

    def test_dashboard_records(self):
        for name in ("complete","double_post","missing_readback"):
            data=json.loads((self.out/"evidence"/f"{name}.json").read_text())
            for route in ("testing","index"):
                part=self.text[route].split(f'id="run-{name}"',1)[1].split("</article>",1)[0]
                self.assertIn(data["decision"]["verdict"],part)
                self.assertIn(f'evidence/{name}.json',part)
                for r in data["after"].get("ledger",[]):
                    self.assertIn(f'<td>#{r["id"]}</td><td>{r["order_id"]}</td><td>{r["amount"]:,}</td>',part)

    def test_contact_boundary_and_source_hashes(self):
        for p in self.pages.values():
            self.assertEqual(p.attrs("form"),[])
            self.assertFalse(any(a.get("href","").startswith(("mailto:","tel:")) for a in p.attrs("a")))
        m=json.loads((self.out/"evidence/provenance.json").read_text())
        for group, base in (("files", ROOT/"evidence"), ("page_sources", ROOT)):
            for row in m[group]:
                self.assertEqual(hashlib.sha256((base / row["file"]).read_bytes()).hexdigest(), row["sha256"])


if __name__=="__main__":
    unittest.main(verbosity=2)
