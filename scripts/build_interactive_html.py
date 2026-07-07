#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import math
from decimal import Decimal
from pathlib import Path

from generate_dat import ProcessorRow, format_decimal, metric_value, parse_newdata

NS = "http://www.w3.org/2000/svg"

SERIES = {
    "cores": {
        "label": "Logical cores",
        "file": "cores.dat",
        "field": "threads",
        "scale": Decimal("1"),
        "color": "#202124",
        "unit": "",
    },
    "frequency": {
        "label": "Frequency (MHz)",
        "file": "frequency.dat",
        "field": "frequency",
        "scale": Decimal("1000"),
        "color": "#16803c",
        "unit": " MHz",
    },
    "specint": {
        "label": "Single-thread performance (SpecInt x 1000)",
        "file": "specint.dat",
        "field": "specint",
        "scale": Decimal("1000"),
        "color": "#1f5fbf",
        "unit": "",
    },
    "transistors": {
        "label": "Transistors (thousands)",
        "file": "transistors.dat",
        "field": "transistors",
        "scale": Decimal("1000000"),
        "color": "#c76719",
        "unit": "k",
    },
    "power": {
        "label": "Typical power (Watts)",
        "file": "watts.dat",
        "field": "tdp",
        "scale": Decimal("1"),
        "color": "#b3261e",
        "unit": " W",
    },
}

WIDTH = 960
HEIGHT = 560
PLOT_X = 76
PLOT_Y = 42
PLOT_W = 710
PLOT_H = 424
LEGEND_X = 812


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build embeddable interactive HTML/SVG charts from newdata.txt."
    )
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--source", default="newdata.txt")
    parser.add_argument("--chart-dir", default="50yrs")
    parser.add_argument("--out-dir", type=Path, default=Path("output/interactive"))
    return parser.parse_args()


def parse_dat(path: Path) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for line in path.read_text().splitlines():
        content = line.split("#", 1)[0].strip()
        if not content or content == "####":
            continue
        parts = content.split()
        if len(parts) < 2:
            continue
        try:
            points.append((float(parts[0]), float(parts[1])))
        except ValueError:
            continue
    return points


def known_metric(row: ProcessorRow, key: str) -> float | None:
    series = SERIES[key]
    value = metric_value(row, series["field"], series["scale"])
    return float(value) if value is not None else None


def source_value(row: ProcessorRow, key: str) -> str:
    field = SERIES[key]["field"]
    raw = getattr(row, field)
    if raw == "??":
        return "unknown"
    if key == "transistors":
        return f"{raw}B"
    if key == "frequency":
        return f"{raw} GHz"
    if key == "power":
        return f"{raw} W"
    if key == "specint":
        return raw
    return raw


def collect_named_points(rows: list[ProcessorRow]) -> list[dict[str, object]]:
    points: list[dict[str, object]] = []
    for row_index, row in enumerate(rows):
        row_id = f"cpu-{row_index}"
        details = {
            "name": row.name,
            "year": row.year_token,
            "chartYear": format_decimal(row.chart_year),
            "transistors": source_value(row, "transistors"),
            "specint": source_value(row, "specint"),
            "frequency": source_value(row, "frequency"),
            "power": source_value(row, "power"),
            "cores": source_value(row, "cores"),
            "note": row.note,
        }
        for key in SERIES:
            value = known_metric(row, key)
            if value is None:
                continue
            points.append(
                {
                    "id": f"{row_id}-{key}",
                    "rowId": row_id,
                    "metric": key,
                    "year": float(row.chart_year),
                    "value": value,
                    "details": details,
                }
            )
    return points


def log_ticks(y_min: float, y_max: float) -> list[float]:
    start = math.floor(math.log10(y_min))
    end = math.ceil(math.log10(y_max))
    return [10**power for power in range(start, end + 1)]


def axis_ticks(x_min: float, x_max: float) -> list[int]:
    start = int(math.ceil(x_min / 5) * 5)
    end = int(math.floor(x_max / 5) * 5)
    return list(range(start, end + 1, 5))


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def build_svg(rows: list[ProcessorRow], background: dict[str, list[tuple[float, float]]]) -> str:
    named_points = collect_named_points(rows)
    all_values = [
        point[1]
        for points in background.values()
        for point in points
        if point[1] > 0
    ] + [float(point["value"]) for point in named_points if float(point["value"]) > 0]
    all_years = [
        point[0]
        for points in background.values()
        for point in points
    ] + [float(point["year"]) for point in named_points]

    x_min = 1970.0
    x_max = max(2022.5, math.ceil(max(all_years or [2022.5]) + 1.0))
    y_min = 0.2
    y_max = 10 ** math.ceil(math.log10(max(all_values or [1])))

    def sx(year: float) -> float:
        return PLOT_X + ((year - x_min) / (x_max - x_min)) * PLOT_W

    def sy(value: float) -> float:
        return PLOT_Y + (math.log10(y_max) - math.log10(value)) / (
            math.log10(y_max) - math.log10(y_min)
        ) * PLOT_H

    elements: list[str] = []
    elements.append(
        f'<svg xmlns="{NS}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        'aria-labelledby="chart-title chart-desc" class="processor-trends">'
    )
    elements.append("<style><![CDATA[")
    elements.append(
        """
        .processor-trends { background: #ffffff; color: #202124; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
        .title { font-size: 22px; font-weight: 700; }
        .subtitle, .axis-label, .legend-text, .source { fill: #555b61; font-size: 12px; }
        .axis, .grid { stroke: #c9ced6; stroke-width: 1; }
        .grid { stroke-dasharray: 2 6; }
        .tick-label { fill: #555b61; font-size: 11px; }
        .series-label { font-size: 12px; font-weight: 650; }
        .background-point { opacity: 0.24; }
        .cpu-point { cursor: pointer; stroke: #ffffff; stroke-width: 1.5; transition: r 120ms ease, opacity 120ms ease, stroke-width 120ms ease; }
        .cpu-point:hover, .cpu-point:focus, .cpu-point.is-active { r: 6.5; opacity: 1; stroke-width: 2; outline: none; }
        .cpu-point.is-related { r: 5.5; opacity: 1; }
        #tooltip-panel { filter: drop-shadow(0 8px 20px rgba(30, 35, 40, 0.18)); pointer-events: none; }
        .tooltip-box { fill: #ffffff; stroke: #aeb6c2; stroke-width: 1; }
        .tooltip-title { fill: #1f2328; font-size: 13px; font-weight: 700; }
        .tooltip-line { fill: #343a40; font-size: 11px; }
        @media (prefers-color-scheme: dark) {
          .processor-trends { background: #111418; color: #e8eaed; }
          .subtitle, .axis-label, .legend-text, .source, .tick-label { fill: #b8c0cc; }
          .axis, .grid { stroke: #3d444d; }
          .tooltip-box { fill: #1b2027; stroke: #59636f; }
          .tooltip-title { fill: #f1f3f4; }
          .tooltip-line { fill: #d7dce2; }
          .cpu-point { stroke: #111418; }
        }
        """
    )
    elements.append("]]></style>")
    elements.append('<title id="chart-title">Interactive Microprocessor Trend Data</title>')
    elements.append(
        '<desc id="chart-desc">Log-scale scatter plot of logical cores, frequency, '
        'single-thread performance, transistor counts, and power. Hover or focus named '
        'processor points to inspect details.</desc>'
    )
    elements.append(f'<text x="{PLOT_X}" y="26" class="title">Microprocessor Trend Data</text>')
    elements.append(
        f'<text x="{PLOT_X}" y="{HEIGHT - 22}" class="source">'
        "Background points come from 50yrs/*.dat; interactive named points come from newdata.txt."
        "</text>"
    )

    # Plot area and grid.
    elements.append(
        f'<line x1="{PLOT_X}" y1="{PLOT_Y + PLOT_H}" x2="{PLOT_X + PLOT_W}" '
        f'y2="{PLOT_Y + PLOT_H}" class="axis" />'
    )
    elements.append(
        f'<line x1="{PLOT_X}" y1="{PLOT_Y}" x2="{PLOT_X}" y2="{PLOT_Y + PLOT_H}" class="axis" />'
    )
    for year in axis_ticks(x_min, x_max):
        x = sx(year)
        elements.append(
            f'<line x1="{x:.2f}" y1="{PLOT_Y}" x2="{x:.2f}" y2="{PLOT_Y + PLOT_H}" class="grid" />'
        )
        elements.append(
            f'<text x="{x:.2f}" y="{PLOT_Y + PLOT_H + 20}" text-anchor="middle" class="tick-label">{year}</text>'
        )
    for value in log_ticks(y_min, y_max):
        y = sy(value)
        label = f"10^{int(math.log10(value))}" if value >= 1 else "0.1"
        elements.append(
            f'<line x1="{PLOT_X}" y1="{y:.2f}" x2="{PLOT_X + PLOT_W}" y2="{y:.2f}" class="grid" />'
        )
        elements.append(
            f'<text x="{PLOT_X - 10}" y="{y + 4:.2f}" text-anchor="end" class="tick-label">{esc(label)}</text>'
        )
    elements.append(
        f'<text x="{PLOT_X + PLOT_W / 2:.2f}" y="{HEIGHT - 58}" text-anchor="middle" class="axis-label">Year</text>'
    )
    elements.append(
        f'<text x="18" y="{PLOT_Y + PLOT_H / 2:.2f}" transform="rotate(-90 18 {PLOT_Y + PLOT_H / 2:.2f})" '
        'text-anchor="middle" class="axis-label">Log-scale metric value</text>'
    )

    # Background trend points.
    for key, series in SERIES.items():
        color = series["color"]
        for year, value in background.get(key, []):
            if value <= 0:
                continue
            elements.append(
                f'<circle class="background-point" cx="{sx(year):.2f}" cy="{sy(value):.2f}" '
                f'r="2.2" fill="{color}" />'
            )

    # Named interactive points.
    point_data: dict[str, object] = {}
    for point in named_points:
        x = sx(float(point["year"]))
        y = sy(float(point["value"]))
        metric = str(point["metric"])
        row_id = str(point["rowId"])
        point_id = str(point["id"])
        series = SERIES[metric]
        point_data[point_id] = point
        aria = (
            f'{point["details"]["name"]}, {series["label"]}, '
            f'{format_decimal(Decimal(str(point["value"])))}'
        )
        elements.append(
            f'<circle id="{esc(point_id)}" class="cpu-point" tabindex="0" role="button" '
            f'aria-label="{esc(aria)}" data-point-id="{esc(point_id)}" data-row-id="{esc(row_id)}" '
            f'cx="{x:.2f}" cy="{y:.2f}" r="4.5" fill="{series["color"]}" />'
        )

    # Legend.
    for index, (key, series) in enumerate(SERIES.items()):
        y = 78 + index * 34
        elements.append(
            f'<circle cx="{LEGEND_X}" cy="{y}" r="5" fill="{series["color"]}" />'
            f'<text x="{LEGEND_X + 14}" y="{y + 4}" class="series-label" fill="{series["color"]}">'
            f'{esc(series["label"])}</text>'
        )
    elements.append(
        f'<text x="{LEGEND_X}" y="270" class="legend-text">'
        "Hover/focus a colored dot for CPU details.</text>"
    )

    elements.append('<g id="tooltip-panel" visibility="hidden"></g>')
    elements.append("<script><![CDATA[")
    elements.append(
        f"""
        const pointData = {json.dumps(point_data, separators=(",", ":"))};
        const metricLabels = {json.dumps({key: value["label"] for key, value in SERIES.items()}, separators=(",", ":"))};
        const svg = document.currentScript.ownerSVGElement;
        const tooltip = svg.getElementById("tooltip-panel");
        const svgNS = "{NS}";

        function clearTooltip() {{
          while (tooltip.firstChild) tooltip.removeChild(tooltip.firstChild);
        }}

        function addText(text, x, y, cls, weight) {{
          const el = document.createElementNS(svgNS, "text");
          el.setAttribute("x", x);
          el.setAttribute("y", y);
          el.setAttribute("class", cls);
          if (weight) el.setAttribute("font-weight", weight);
          el.textContent = text;
          tooltip.appendChild(el);
          return el;
        }}

        function clamp(value, min, max) {{
          return Math.max(min, Math.min(max, value));
        }}

        function placeTooltip(cx, cy, width, height) {{
          const gap = 22;
          const margin = 12;
          const rightSpace = {WIDTH} - cx;
          const leftSpace = cx;
          const preferLeft = rightSpace < width + gap + margin && leftSpace > rightSpace;
          const x = preferLeft ? cx - width - gap : cx + gap;
          const preferAbove = cy > {HEIGHT} * 0.62;
          const y = preferAbove ? cy - height - gap : cy + gap;
          return {{
            x: clamp(x, margin, {WIDTH} - width - margin),
            y: clamp(y, margin, {HEIGHT} - height - margin)
          }};
        }}

        function showTooltip(target) {{
          const id = target.dataset.pointId;
          const point = pointData[id];
          if (!point) return;
          const details = point.details;
          const rows = [
            `${{metricLabels[point.metric]}}: ${{Number(point.value).toLocaleString()}}`,
            `Year: ${{details.year}}`,
            `Transistors: ${{details.transistors}}`,
            `Frequency: ${{details.frequency}}`,
            `SpecInt: ${{details.specint}}`,
            `Power: ${{details.power}}`,
            `Logical cores: ${{details.cores}}`
          ];
          if (details.note) rows.push(details.note);

          svg.querySelectorAll(".cpu-point").forEach((el) => {{
            el.classList.toggle("is-active", el.dataset.pointId === id);
            el.classList.toggle("is-related", el.dataset.rowId === point.rowId && el.dataset.pointId !== id);
          }});

          clearTooltip();
          const cx = Number(target.getAttribute("cx"));
          const cy = Number(target.getAttribute("cy"));
          const boxWidth = 260;
          const boxHeight = 42 + rows.length * 17;
          const position = placeTooltip(cx, cy, boxWidth, boxHeight);
          const x = position.x;
          const y = position.y;
          const rect = document.createElementNS(svgNS, "rect");
          rect.setAttribute("x", x);
          rect.setAttribute("y", y);
          rect.setAttribute("width", boxWidth);
          rect.setAttribute("height", boxHeight);
          rect.setAttribute("rx", 6);
          rect.setAttribute("class", "tooltip-box");
          tooltip.appendChild(rect);
          addText(details.name, x + 12, y + 20, "tooltip-title");
          rows.forEach((line, index) => addText(line, x + 12, y + 42 + index * 17, "tooltip-line"));
          tooltip.setAttribute("visibility", "visible");
        }}

        function hideTooltip() {{
          tooltip.setAttribute("visibility", "hidden");
          clearTooltip();
          svg.querySelectorAll(".cpu-point").forEach((el) => {{
            el.classList.remove("is-active", "is-related");
          }});
        }}

        svg.querySelectorAll(".cpu-point").forEach((point) => {{
          point.addEventListener("mouseenter", () => showTooltip(point));
          point.addEventListener("focus", () => showTooltip(point));
          point.addEventListener("mouseleave", hideTooltip);
          point.addEventListener("blur", hideTooltip);
        }});
        """
    )
    elements.append("]]></script>")
    elements.append("</svg>")
    return "\n".join(elements)


def build_html(svg: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Interactive Microprocessor Trend Data</title>
  <style>
    :root {{
      color-scheme: light dark;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #ffffff;
      color: #202124;
    }}
    body {{
      margin: 0;
      min-width: 320px;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 16px;
    }}
    .embed-shell {{
      width: 100%;
      overflow-x: auto;
    }}
    svg {{
      display: block;
      width: 100%;
      min-width: 760px;
      height: auto;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        background: #111418;
        color: #e8eaed;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <div class="embed-shell">
{svg}
    </div>
  </main>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    source = repo / args.source
    chart_dir = repo / args.chart_dir
    out_dir = args.out_dir if args.out_dir.is_absolute() else repo / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = parse_newdata(source)
    background = {
        key: parse_dat(chart_dir / str(series["file"]))
        for key, series in SERIES.items()
    }
    svg = build_svg(rows, background)
    html_doc = build_html(svg)

    svg_path = out_dir / "processor-trends.svg"
    html_path = out_dir / "processor-trends.html"
    svg_path.write_text(svg)
    html_path.write_text(html_doc)
    print(f"wrote {html_path.relative_to(repo)}")
    print(f"wrote {svg_path.relative_to(repo)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
