#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
if not repo.exists():
    raise SystemExit(f"Repo not found: {repo}")


def ignored(path: Path) -> bool:
    return any(part in {".git", "output"} for part in path.parts)


print(f"Repo: {repo.resolve()}")
print("\nLikely data files:")
for p in sorted(repo.rglob("*.dat")):
    if not ignored(p):
        print("  ", p.relative_to(repo))
for name in ["newdata.txt", "README.md"]:
    p = repo / name
    if p.exists():
        print("  ", p.relative_to(repo))

print("\nGnuplot scripts:")
for p in sorted(repo.rglob("*.gnuplot")):
    if not ignored(p):
        print("  ", p.relative_to(repo))

print("\nTop-level dirs:")
for p in sorted(repo.iterdir()):
    if p.is_dir() and not p.name.startswith(".git") and p.name != "output":
        print("  ", p.name)
