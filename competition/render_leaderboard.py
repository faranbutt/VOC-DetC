import csv
import html
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "leaderboard" / "leaderboard.csv"
MD_PATH = ROOT / "leaderboard" / "leaderboard.md"
HTML_PATH = ROOT / "docs" / "index.html"


def score(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else float("-inf")
    except (TypeError, ValueError):
        return float("-inf")


def cell(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def main():
    rows = []
    if CSV_PATH.exists():
        with CSV_PATH.open("r", newline="", encoding="utf-8") as handle:
            rows = [
                row for row in csv.DictReader(handle)
                if (row.get("team") or "").strip()
            ]

    rows.sort(key=lambda row: (-score(row.get("AP")), row.get("timestamp_utc", "")))

    markdown = [
        "# ViSC-Bench Leaderboard\n\n",
        "| Rank | Team | AP | AP50 | AP75 | Model | Date (UTC) |\n",
        "|---:|---|---:|---:|---:|---|---|\n",
    ]
    html_rows = []
    for rank, row in enumerate(rows, start=1):
        ap = row.get("AP", "")
        markdown.append(
            f"| {rank} | {row.get('team', '')} | {ap} | "
            f"{row.get('AP50', '')} | {row.get('AP75', '')} | "
            f"{row.get('model', '')} | {row.get('timestamp_utc', '')} |\n"
        )
        html_rows.append(
            "<tr>"
            f'<td class="rank">{rank}</td>'
            f"<td><strong>{cell(row.get('team'))}</strong></td>"
            f'<td class="score">{cell(f"{score(ap):.4f}" if score(ap) != float("-inf") else "—")}</td>'
            f"<td>{cell(row.get('AP50'))}</td>"
            f"<td>{cell(row.get('AP75'))}</td>"
            f"<td>{cell(row.get('model'))}</td>"
            f"<td>{cell(row.get('timestamp_utc'))}</td>"
            "</tr>"
        )

    MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text("".join(markdown), encoding="utf-8")

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    empty_row = '<tr><td colspan="7" class="empty">No valid submissions yet. Be the first!</td></tr>'
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Official ViSC-Bench corruption-robust grape instance segmentation competition leaderboard.">
<title>ViSC-Bench | Leaderboard</title>
<style>
:root {{ color-scheme: dark; --bg:#0b1020; --panel:#121b2d; --line:#26344c; --text:#edf2fa; --muted:#9eacc2; --accent:#8db5ff; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; padding:40px 20px; background:var(--bg); color:var(--text); font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif; }}
main {{ max-width:1120px; margin:0 auto; }}
h1 {{ margin:0 0 8px; font-size:clamp(2rem,5vw,3rem); letter-spacing:-.04em; }}
.subtitle {{ margin:0 0 28px; color:var(--muted); }}
.panel {{ overflow-x:auto; border:1px solid var(--line); border-radius:14px; background:var(--panel); }}
table {{ width:100%; border-collapse:collapse; min-width:720px; }}
th,td {{ padding:14px 16px; text-align:left; border-bottom:1px solid var(--line); }}
th {{ color:var(--muted); font-size:.78rem; letter-spacing:.07em; text-transform:uppercase; }}
tbody tr:last-child td {{ border-bottom:0; }}
tbody tr:hover {{ background:#ffffff08; }}
.rank,.score {{ color:var(--accent); font-weight:700; }}
.empty {{ padding:32px; color:var(--muted); text-align:center; }}
footer {{ margin-top:18px; color:var(--muted); font-size:.85rem; }}
@media(max-width:600px) {{ body {{ padding:28px 12px; }} th,td {{ padding:11px 12px; }} }}
</style>
</head>
<body>
<main>
  <h1>ViSC-Bench</h1>
  <p class="subtitle">Corruption-Robust Grape Instance Segmentation Benchmark · Official Leaderboard</p>
  <section class="panel" aria-label="Competition leaderboard">
    <table>
      <thead><tr><th>Rank</th><th>Team</th><th>AP (0.50:0.95)</th><th>AP50</th><th>AP75</th><th>Model</th><th>Date (UTC)</th></tr></thead>
      <tbody>{''.join(html_rows) if html_rows else empty_row}</tbody>
    </table>
  </section>
  <footer>Last updated: {updated}. Scores are computed by the official evaluation pipeline.</footer>
</main>
</body>
</html>
"""
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(html_doc, encoding="utf-8")


if __name__ == "__main__":
    main()
