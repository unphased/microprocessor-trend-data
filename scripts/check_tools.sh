#!/usr/bin/env bash
set -euo pipefail

missing=0
for tool in git make python3 gnuplot; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "ok: $tool -> $(command -v "$tool")"
  else
    echo "missing: $tool"
    missing=1
  fi
done

# Optional converters used by many gnuplot/EPS workflows.
for tool in gs convert magick; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "optional ok: $tool -> $(command -v "$tool")"
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo
  echo "Install on openSUSE: sudo zypper install git make gnuplot ghostscript ImageMagick python3"
  exit 1
fi
