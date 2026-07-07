#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-.}"
OUT="${2:-output}"

if [[ ! -d "$REPO" ]]; then
  echo "Missing repo: $REPO"
  exit 1
fi

REPO="$(cd "$REPO" && pwd)"
if [[ "$OUT" != /* ]]; then
  OUT="$(pwd)/$OUT"
fi

if ! command -v gnuplot >/dev/null 2>&1; then
  echo "Missing gnuplot. On openSUSE: sudo zypper install gnuplot"
  exit 1
fi

if [[ -z "$OUT" || "$OUT" == "/" ]]; then
  echo "Refusing unsafe output directory: $OUT"
  exit 1
fi

rm -rf "$OUT/rendered"
mkdir -p "$OUT/rendered"

mapfile -t scripts < <(
  find "$REPO" \
    \( -path '*/.git' -o -path "$OUT" -o -path "$OUT/*" \) -prune \
    -o -name '*.gnuplot' -print | sort
)
if [[ ${#scripts[@]} -eq 0 ]]; then
  echo "No .gnuplot files found. Run make inspect and check repo layout."
  exit 1
fi

echo "Found ${#scripts[@]} gnuplot scripts. Rendering each in its own directory..."

for script in "${scripts[@]}"; do
  script_dir="$(dirname "$script")"
  rel="${script#$REPO/}"
  safe="${rel//\//__}"
  render_dir="$OUT/rendered/${safe%.gnuplot}"
  work_dir="$(mktemp -d)"
  mkdir -p "$render_dir"

  echo "Rendering: $rel"
  cp -R "$script_dir"/. "$work_dir"/
  (
    cd "$work_dir"
    # Run gnuplot from the script directory so relative data paths still work.
    gnuplot "$(basename "$script")"
  ) || {
    echo "WARN: failed rendering $rel"
    rm -rf "$work_dir"
    continue
  }

  # Copy newly produced common output types from script dir.
  find "$work_dir" -maxdepth 1 \( -name '*.eps' -o -name '*.png' -o -name '*.pdf' -o -name '*.svg' \) -type f -print0 \
    | xargs -0 -I{} cp -f {} "$render_dir/" || true
  rm -rf "$work_dir"
done

echo
find "$OUT/rendered" -type f | sort || true
