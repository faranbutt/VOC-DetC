import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

HEADERS = [
    "timestamp_utc", "team", "run_id", "author_type", "model", "notes",
    "submission_file",
    "AP", "AP50", "AP75",
    "AP_small", "AP_medium", "AP_large",
    "AR1", "AR10", "AR100", "prediction_count",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-file", required=True, type=Path)
    parser.add_argument("--metrics-file", required=True, type=Path)
    parser.add_argument("--submission-file", required=True)
    args = parser.parse_args()

    cfg = yaml.safe_load(open("competition/config.yaml", encoding="utf-8"))
    meta = json.loads(args.metadata_file.read_text(encoding="utf-8"))
    metrics = json.loads(args.metrics_file.read_text(encoding="utf-8"))

    team = str(meta.get("team", "")).strip()

    if not team:
        raise SystemExit("Error: Missing team name in submission metadata.")
    csv_path = Path("leaderboard/leaderboard.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    if csv_path.exists():
        with csv_path.open("r", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    if cfg.get("one_submission_per_team", True) and any(
    (r.get("team") or "").strip().casefold() == team.strip().casefold()
    for r in rows):
        raise SystemExit(f"Submission rejected: team '{team}' already exists.")

    row = {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "team": team,
        "run_id": str(meta.get("run_id", "run_01")),
        "author_type": str(meta.get("author_type", "human")),
        "model": str(meta.get("model", "unknown")),
        "notes": str(meta.get("notes", "")),
        "submission_file": args.submission_file,
    }
    row.update(metrics)
    rows.append(row)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Leaderboard updated: {team} / AP={row.get('AP')}")


if __name__ == "__main__":
    main()