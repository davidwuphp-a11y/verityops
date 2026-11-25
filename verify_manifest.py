"""Verify the release checksums using only the Python standard library."""
from hashlib import sha256
from pathlib import Path, PurePosixPath
import re


def main():
    root = Path(__file__).resolve().parent
    seen = set()
    lines = (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    for line in lines:
        entry = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_./-]+)", line)
        if not entry:
            raise SystemExit("Malformed checksum entry")
        expected, name = entry.groups()
        rel = PurePosixPath(name)
        if rel.is_absolute() or ".." in rel.parts or name in seen:
            raise SystemExit("Invalid or repeated checksum path")
        seen.add(name)
        path = root / rel
        if not path.resolve().is_relative_to(root) or not path.is_file():
            raise SystemExit(f"Missing or invalid release file: {name}")
        if sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit(f"Checksum mismatch: {name}")
    if "RELEASE_MANIFEST.json" not in seen:
        raise SystemExit("Missing release manifest entry")
    print(f"Verified {len(seen)} release file checksums.")


if __name__ == "__main__":
    main()
