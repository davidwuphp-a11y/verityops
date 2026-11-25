"""Generate static pages from a reviewed locale and frozen evidence."""
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
from html import escape
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
EVIDENCE=ROOT/"evidence"

def build(base_url=None, locale="en", output=None):
    if not re.fullmatch(r"[a-z]{2}(?:-[A-Za-z]{2,4})?",locale):
        raise ValueError("Unsupported locale identifier")
    source = ROOT/"content"/locale/"views.py"
    if not source.is_file():
        raise ValueError(f"No reviewed content pack for {locale}")
    spec = importlib.util.spec_from_file_location("localized_views", source)
    view = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(view)
    LANG, NAV, PAGES = view.LANG, view.NAV, view.PAGES
    url, header, footer = view.url, view.header, view.footer
    if LANG["locale"] != locale or set(NAV) != set(PAGES):
        raise ValueError("Inconsistent locale or page map")
    OUT = Path(output).resolve() if output else ROOT/"dist"
    if locale != "en":
        OUT = OUT/locale.lower()
        if base_url:
            base_url = base_url.rstrip("/")+"/"+locale.lower()+"/"
    if base_url:
        parts = urlparse(base_url)
        if parts.scheme != "https" or not parts.netloc or parts.query or parts.fragment:
            raise ValueError("Provide the final HTTPS website base, including any repository path.")
        base_url = base_url.rstrip("/") + "/"
    manifest = json.loads((EVIDENCE/"provenance.json").read_text(encoding="utf-8"))
    for item in manifest["page_sources"]:
        if hashlib.sha256((ROOT/item["file"]).read_bytes()).hexdigest()!=item["sha256"]:
            raise ValueError("Case-study source hash mismatch: "+item["file"])
    for item in manifest["files"]:
        if hashlib.sha256((EVIDENCE/item["file"]).read_bytes()).hexdigest()!=item["sha256"]:
            raise ValueError("Packaged evidence hash mismatch: "+item["file"])
    OUT.mkdir(parents=True,exist_ok=True)
    for folder in ("assets","evidence"):
        files = ROOT/folder
        shutil.copytree(files, OUT/folder, dirs_exist_ok=True)
    (OUT/".nojekyll").touch()
    for page,render in PAGES.items():
        name = LANG["home_title"] if page=="index" else f"{NAV[page]} | VerityOps"
        desc = escape(LANG["descriptions"][page], quote=True)
        current = escape(base_url+url(page),quote=True) if base_url else None
        social = escape((base_url or "")+"assets/social.png",quote=True)
        canonical = f'<link rel="canonical" href="{current}"><meta property="og:url" content="{current}">' if current else ""
        html=f"""<!doctype html><html lang="{LANG['locale']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{escape(name)}</title><meta name="description" content="{desc}"><meta name="theme-color" content="#0a1322">
        <meta property="og:type" content="website"><meta property="og:site_name" content="VerityOps"><meta property="og:title" content="{escape(name)}">
        <meta property="og:description" content="{desc}"><meta property="og:locale" content="{escape(LANG['og_locale'])}"><meta property="og:image" content="{social}"><meta property="og:image:alt" content="VerityOps — Trust the outcome. Verify the execution.">{canonical}
        <meta name="twitter:card" content="summary_large_image"><link rel="icon" type="image/svg+xml" href="assets/brand.svg"><link rel="stylesheet" href="assets/site.css"><script src="assets/site.js" defer></script></head><body>
        {header(page)}<main id="main">{render()}</main>{footer()}</body></html>"""
        (OUT/url(page)).write_text(html,encoding="utf-8")
    print(f"Built {len(PAGES)} {locale} pages in {OUT}")

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", help="Verified HTTPS hosting base for absolute social and canonical URLs")
    parser.add_argument("--locale", default="en", help="Reviewed locale pack under content/")
    parser.add_argument("--output", help="Static output directory, default dist")
    args=parser.parse_args()
    build(args.base_url,args.locale,args.output)
