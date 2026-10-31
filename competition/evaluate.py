import argparse
import json
from pathlib import Path

from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval


ZERO_METRICS = {
    "AP": 0.0, "AP50": 0.0, "AP75": 0.0,
    "AP_small": 0.0, "AP_medium": 0.0, "AP_large": 0.0,
    "AR1": 0.0, "AR10": 0.0, "AR100": 0.0,
    "prediction_count": 0,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground-truth", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--task", choices=["bbox", "segm"], required=True)
    args = parser.parse_args()

    preds = json.loads(args.predictions.read_text(encoding="utf-8"))
    gt_data = json.loads(args.ground_truth.read_text(encoding="utf-8"))

    allowed_image_ids = {int(x["id"]) for x in gt_data["images"]}
    allowed_category_ids = {int(c["id"]) for c in gt_data["categories"]}

    if not preds:
        print(json.dumps(ZERO_METRICS, indent=2))
        return

    normalized = []
    for pred in preds:
        p = dict(pred)
        if args.task == "segm":
            p.pop("bbox", None)
        normalized.append(p)

    gt = COCO(str(args.ground_truth))
    gt.dataset.setdefault("info", {})
    gt.dataset.setdefault("licenses", [])

    dt = gt.loadRes(normalized)
    evaluator = COCOeval(gt, dt, iouType=args.task)
    evaluator.params.imgIds = sorted(allowed_image_ids)
    evaluator.params.catIds = sorted(allowed_category_ids)
    evaluator.evaluate()
    evaluator.accumulate()

    s = evaluator.stats
    metrics = {
        "AP": float(s[0]),
        "AP50": float(s[1]),
        "AP75": float(s[2]),
        "AP_small": float(s[3]),
        "AP_medium": float(s[4]),
        "AP_large": float(s[5]),
        "AR1": float(s[6]),
        "AR10": float(s[7]),
        "AR100": float(s[8]),
        "prediction_count": len(preds),
    }
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()