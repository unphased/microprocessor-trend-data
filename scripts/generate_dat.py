#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

METRICS = {
    "cores.dat": ("threads", Decimal("1")),
    "frequency.dat": ("frequency", Decimal("1000")),
    "specint.dat": ("specint", Decimal("1000")),
    "transistors.dat": ("transistors", Decimal("1000000")),
    "watts.dat": ("tdp", Decimal("1")),
}

CHART_LIMITS = {
    "40yrs": Decimal("2015"),
    "42yrs": Decimal("2018"),
    "48yrs": Decimal("2020"),
    "50yrs": None,
}

YEAR_RE = re.compile(r"^\d{4}\.\d+$")


@dataclass
class ProcessorRow:
    name: str
    year_token: str
    chart_year: Decimal
    transistors: str
    specint: str
    frequency: str
    tdp: str
    threads: str
    note: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Regenerate plot-ready .dat files from newdata.txt."
    )
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--source", default="newdata.txt")
    parser.add_argument("--check", action="store_true", help="show diffs without writing")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="rewrite the whole derived section instead of preserving existing rows",
    )
    return parser.parse_args()


def chart_year(year_token: str, seen: dict[str, int]) -> Decimal:
    year, suffix = year_token.split(".", 1)
    if len(suffix) == 2 and suffix.isdigit() and 1 <= int(suffix) <= 12:
        value = Decimal(year) + (Decimal(suffix) / Decimal(12))
    else:
        value = Decimal(year_token)

    base = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    key = f"{base:.2f}"
    offset = seen.get(key, 0)
    seen[key] = offset + 1
    return base + (Decimal("0.01") * offset)


def format_decimal(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    return text[:-2] if text.endswith(".0") else text


def parse_newdata(path: Path) -> list[ProcessorRow]:
    rows: list[ProcessorRow] = []
    seen_years: dict[str, int] = {}

    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        content, _, comment = line.partition("#")
        content = content.strip()
        if not content:
            continue

        tokens = content.split()
        year_index = next((i for i, token in enumerate(tokens) if YEAR_RE.match(token)), None)
        if year_index is None:
            continue
        if len(tokens) < year_index + 6:
            raise SystemExit(f"{path}:{line_number}: expected six fields after processor name")

        name = " ".join(tokens[:year_index])
        year_token = tokens[year_index]
        rows.append(
            ProcessorRow(
                name=name,
                year_token=year_token,
                chart_year=chart_year(year_token, seen_years),
                transistors=tokens[year_index + 1],
                specint=tokens[year_index + 2],
                frequency=tokens[year_index + 3],
                tdp=tokens[year_index + 4],
                threads=tokens[year_index + 5],
                note=comment.strip(),
            )
        )

    return rows


def is_known(value: str) -> bool:
    return value != "??"


def metric_value(row: ProcessorRow, field: str, scale: Decimal) -> str | None:
    raw = getattr(row, field)
    if not is_known(raw):
        return None

    value = Decimal(raw) * scale
    return format_decimal(value)


def generated_lines(rows: list[ProcessorRow], chart: str, filename: str) -> list[str]:
    field, scale = METRICS[filename]
    limit = CHART_LIMITS[chart]
    lines: list[str] = []

    for row in rows:
        if limit is not None and row.chart_year >= limit:
            continue

        value = metric_value(row, field, scale)
        if value is None:
            continue
        lines.append(f"{format_decimal(row.chart_year):<9}  {value}\n")

    return lines


def split_at_last_marker(lines: list[str], path: Path) -> tuple[list[str], list[str]]:
    marker_indexes = [i for i, line in enumerate(lines) if line.strip() == "####"]
    if not marker_indexes:
        raise SystemExit(f"{path}: no #### marker found")

    index = marker_indexes[-1] + 1
    return lines[:index], lines[index:]


def build_file(path: Path, rows: list[ProcessorRow], rebuild: bool) -> list[str]:
    prefix, old_generated = split_at_last_marker(path.read_text().splitlines(True), path)
    new_generated = generated_lines(rows, path.parent.name, path.name)

    if not rebuild:
        # The upstream .dat files contain hand-positioned years and a few
        # historical value quirks. Preserve those rows by default and only append
        # rows that are newly present in newdata.txt.
        if len(new_generated) <= len(old_generated):
            new_generated = old_generated
        else:
            new_generated = old_generated + new_generated[len(old_generated) :]

    return prefix + new_generated


def show_diff(path: Path, old: list[str], new: list[str]) -> bool:
    if old == new:
        return False

    print(
        "".join(
            difflib.unified_diff(
                old,
                new,
                fromfile=str(path),
                tofile=f"{path} (generated)",
            )
        ),
        end="",
    )
    return True


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    rows = parse_newdata(repo / args.source)

    changed = False
    for chart in CHART_LIMITS:
        for filename in METRICS:
            path = repo / chart / filename
            old = path.read_text().splitlines(True)
            new = build_file(path, rows, args.rebuild)
            if args.check:
                changed = show_diff(path, old, new) or changed
            elif old != new:
                path.write_text("".join(new))
                changed = True
                print(f"updated {path.relative_to(repo)}")

    if args.check and changed:
        return 1
    if not changed:
        print("generated .dat files are already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
