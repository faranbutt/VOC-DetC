import argparse
import json
import math
import sys
from contextlib import redirect_stdout
from pathlib import Path

from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval

METRIC_KEYS = (
    "AP", "AP50", "AP75", "AP_small", "AP_medium", "AP_large",
    "AR1", "AR10", "AR100",
)

def evaluate(ground_truth_path: Path, predictions_path: Path, iou_type: str) -> dict:
    predictions = json.loads(predictions_path.read_text(encoding="utf-8"))
    gt_data = json.loads(ground_truth_path.read_text(encoding="utf-8"))
    if not isinstance(predictions, list):
        raise ValueError("Predictions must be a JSON array.")
    if not isinstance(gt_data, dict):
        raise ValueError("Ground truth must be a COCO JSON object.")
    if not predictions:
        return {**{key: 0.0 for key in METRIC_KEYS}, "prediction_count": 0}

    image_ids = sorted(int(image["id"]) for image in gt_data["images"])
    category_ids = sorted(int(category["id"]) for category in gt_data["categories"])

    # Keep pycocotools diagnostics off stdout; stdout is reserved for JSON.
    with redirect_stdout(sys.stderr):
        coco_gt = COCO(str(ground_truth_path))
        coco_gt.dataset.setdefault("info", {})
        coco_gt.dataset.setdefault("licenses", [])
        coco_dt = coco_gt.loadRes(predictions)
        evaluator = COCOeval(coco_gt, coco_dt, iouType=iou_type)
        evaluator.params.imgIds = image_ids
        evaluator.params.catIds = category_ids
        evaluator.evaluate()
        evaluator.accumulate()
        # stats is populated by summarize(), not accumulate().
        evaluator.summarize()
        stats = evaluator.stats

    if len(stats) < 9:
        raise RuntimeError(f"COCOeval returned {len(stats)} summary values; expected at least 9.")
    values = [float(value) for value in stats[:9]]
    if any(not math.isfinite(value) for value in values):
        raise RuntimeError("COCOeval returned a non-finite metric.")
    return {
        key: (value if value >= 0 else 0.0)
        for key, value in zip(METRIC_KEYS, values)
    } | {"prediction_count": len(predictions)}

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate COCO-format competition predictions.")
    parser.add_argument("--ground-truth", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--task", choices=("bbox", "segm"), required=True)
    parser.add_argument("--output", type=Path, help="Optional path for metrics JSON.")
    args = parser.parse_args()
    metrics = evaluate(args.ground_truth, args.predictions, args.task)
    serialized = json.dumps(metrics, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")

if __name__ == "__main__":
    main()
