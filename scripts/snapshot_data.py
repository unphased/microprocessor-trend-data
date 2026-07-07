#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sys
from pathlib import Path

repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output/data-snapshot")
if not repo.exists():
    raise SystemExit(f"Repo not found: {repo}")

if not out.is_absolute():
    out = repo / out

if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)

patterns = ["*.dat", "*.txt", "*.gnuplot", "*.gp"]
count = 0
for pattern in patterns:
    for src in repo.rglob(pattern):
        if ".git" in src.parts or "output" in src.relative_to(repo).parts:
            continue
        dst = out / src.relative_to(repo)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        count += 1
print(f"Copied {count} files to {out}")
