import argparse
import csv
import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

HEADERS = [
    "timestamp_utc", "team", "run_id", "author_type", "model", "notes",
    "submission_file", "AP", "AP50", "AP75", "AP_small", "AP_medium",
    "AP_large", "AR1", "AR10", "AR100", "prediction_count",
]
METRIC_KEYS = HEADERS[7:]


def load_json(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Required JSON file is missing or empty: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def safe_text(value, field: str, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) > limit or any(ord(char) < 32 for char in text):
        raise ValueError(f"Invalid {field}: must be at most {limit} printable characters.")
    # Prevent spreadsheet formula execution when CSV is opened in office software.
    if text.startswith(("=", "+", "-", "@")):
        text = "'" + text
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-file", required=True, type=Path)
    parser.add_argument("--metrics-file", required=True, type=Path)
    parser.add_argument("--submission-file", required=True)
    args = parser.parse_args()

    metadata = load_json(args.metadata_file)
    metrics = load_json(args.metrics_file)
    team = safe_text(metadata.get("team"), "team", 80)
    if not team:
        raise ValueError("Metadata is missing a team name.")

    normalized_metrics = {}
    for key in METRIC_KEYS:
        if key not in metrics:
            raise ValueError(f"Metrics JSON is missing required field: {key}")
        value = float(metrics[key])
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"Metric {key} must be finite and non-negative.")
        normalized_metrics[key] = int(value) if key == "prediction_count" else value

    config = yaml.safe_load(Path("competition/config.yaml").read_text(encoding="utf-8")) or {}
    csv_path = Path("leaderboard/leaderboard.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    if csv_path.exists() and csv_path.stat().st_size:
        with csv_path.open("r", newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

    if config.get("one_submission_per_team", True):
        existing = {str(row.get("team", "")).casefold() for row in rows}
        if team.casefold() in existing:
            raise SystemExit(f"Submission rejected: team '{team}' already has a leaderboard entry.")

    row = {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "team": team,
        "run_id": safe_text(metadata.get("run_id", "run_01"), "run_id", 100),
        "author_type": safe_text(metadata.get("author_type", "human"), "author_type", 40),
        "model": safe_text(metadata.get("model", "unknown"), "model", 160),
        "notes": safe_text(metadata.get("notes", ""), "notes", 500),
        "submission_file": safe_text(args.submission_file, "submission reference", 120),
    }
    row.update(normalized_metrics)
    rows.append(row)

    # Atomic replacement prevents interrupted writes from truncating the public CSV.
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", newline="", encoding="utf-8", dir=csv_path.parent, delete=False
        ) as handle:
            temporary_path = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=HEADERS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary_path, csv_path)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()

    print(f"Leaderboard updated: {team} / AP={row['AP']:.6f}")


if __name__ == "__main__":
    main()
