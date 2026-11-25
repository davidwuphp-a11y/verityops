"""Permit exactly the reviewed website payload in the deployment artifact."""
from pathlib import Path
import sys

ROUTES = "index platform how-it-works use-cases testing research about contact".split()
ASSETS = "brand.svg stack.svg social.png inter-variable.woff2 Inter-LICENSE.txt site.css site.js".split()
EVIDENCE = "complete double_post missing_readback duplicate-replay task-c-US task-c-CN provenance".split()

def expected():
    return {".nojekyll", "LICENSE.txt", *(f"{p}.html" for p in ROUTES),
            *(f"assets/{p}" for p in ASSETS), *(f"evidence/{p}.json" for p in EVIDENCE)}

if __name__ == "__main__":
    root = Path(sys.argv[1])
    items = list(root.rglob("*"))
    if any(p.is_symlink() for p in items):
        raise SystemExit("Unexpected link in export")
    actual = {p.relative_to(root).as_posix() for p in items if p.is_file()}
    if actual != expected():
        raise SystemExit(f"Unexpected or missing public files: {sorted(actual ^ expected())}")
    print(f"Verified {len(actual)} reviewed public files")
