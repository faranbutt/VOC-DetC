import csv
import html
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "leaderboard" / "leaderboard.csv"
MD_PATH = ROOT / "leaderboard" / "leaderboard.md"
HTML_PATH = ROOT / "docs" / "index.html"


def safe_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("-inf")


def main():
    rows = []
    if CSV_PATH.exists():
        with CSV_PATH.open("r", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if (r.get("team") or "").strip()]

    rows.sort(key=lambda r: (-safe_float(r.get("AP")), r.get("timestamp_utc", "")))

    md = ["# Leaderboard\n\n",
          "| Rank | Team | AP | AP50 | AP75 | Author | Model | Run | Date (UTC) | Notes |\n",
          "|---:|---|---:|---:|---:|---|---|---|---|---|\n"]

    html_rows = []
    for i, r in enumerate(rows, start=1):
        ap = r.get("AP", "0")
        md.append(
            f"| {i} | {r.get('team','')} | **{ap}** | {r.get('AP50','')} | "
            f"{r.get('AP75','')} | {r.get('author_type','')} | "
            f"`{r.get('model','')}` | {r.get('run_id','')} | "
            f"{r.get('timestamp_utc','')} | {r.get('notes','')} |\n"
        )
        html_rows.append(
            "<tr>"
            f"<td>{i}</td>"
            f"<td>{html.escape(str(r.get('team','')))}</td>"
            f"<td><strong>{html.escape(str(ap))}</strong></td>"
            f"<td>{html.escape(str(r.get('AP50','')))}</td>"
            f"<td>{html.escape(str(r.get('AP75','')))}</td>"
            f"<td>{html.escape(str(r.get('author_type','')))}</td>"
            f"<td>{html.escape(str(r.get('model','')))}</td>"
            f"<td>{html.escape(str(r.get('run_id','')))}</td>"
            f"<td>{html.escape(str(r.get('timestamp_utc','')))}</td>"
            f"<td>{html.escape(str(r.get('notes','')))}</td>"
            "</tr>"
        )

    MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text("".join(md), encoding="utf-8")

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Image Competition Leaderboard</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; margin: 40px; background:#f4f4f9; color:#222; }}
.container {{ max-width:1200px; margin:auto; }}
table {{ border-collapse:collapse; width:100%; background:white; border-radius:8px; overflow:hidden; box-shadow:0 4px 6px rgba(0,0,0,.1); }}
th, td {{ padding:12px; text-align:left; border-bottom:1px solid #eee; }}
th {{ background:#2c3e50; color:white; font-size:13px; text-transform:uppercase; }}
tr:hover {{ background:#f9f9f9; }}
h1 {{ text-align:center; color:#2c3e50; }}
.timestamp {{ text-align:center; color:#666; font-size:.9em; margin-bottom:24px; }}
</style>
</head>
<body>
<div class="container">
<h1>Image Competition Leaderboard</h1>
<p class="timestamp">Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
<table>
<thead>
<tr>
<th>Rank</th><th>Team</th><th>AP</th><th>AP50</th><th>AP75</th>
<th>Author</th><th>Model</th><th>Run</th><th>Date (UTC)</th><th>Notes</th>
</tr>
</thead>
<tbody>
{''.join(html_rows)}
</tbody>
</table>
</div>
</body>
</html>
"""
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(html_doc, encoding="utf-8")


if __name__ == "__main__":
    main()