import argparse
import json
import sys
from pathlib import Path

try:
    from pycocotools.coco import COCO
    from pycocotools.cocoeval import COCOeval
except ImportError:
    sys.stderr.write("pycocotools not installed\n")
    sys.exit(1)

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

    metrics = ZERO_METRICS.copy()

    try:
        preds = json.loads(args.predictions.read_text(encoding="utf-8"))
        gt_data = json.loads(args.ground_truth.read_text(encoding="utf-8"))
        
        if not preds:
            print(json.dumps(metrics, indent=2))
            return

        metrics["prediction_count"] = len(preds)

        allowed_image_ids = {int(x["id"]) for x in gt_data["images"]}
        allowed_category_ids = {int(c["id"]) for c in gt_data["categories"]}

        normalized = []
        for pred in preds:
            p = dict(pred)
            if args.task == "segm":
                p.pop("bbox", None)
            # Clean up invalid boxes to prevent pycocotools from crashing
            if args.task == "bbox" and "bbox" in p:
                bbox = p["bbox"]
                if float(bbox[2]) <= 0 or float(bbox[3]) <= 0:
                    continue 
            normalized.append(p)

        if not normalized:
            print(json.dumps(metrics, indent=2))
            return

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
        
        if len(s) >= 9:
            metrics = {
                "AP": float(s[0]) if s[0] > -1 else 0.0,
                "AP50": float(s[1]) if s[1] > -1 else 0.0,
                "AP75": float(s[2]) if s[2] > -1 else 0.0,
                "AP_small": float(s[3]) if s[3] > -1 else 0.0,
                "AP_medium": float(s[4]) if s[4] > -1 else 0.0,
                "AP_large": float(s[5]) if s[5] > -1 else 0.0,
                "AR1": float(s[6]) if s[6] > -1 else 0.0,
                "AR10": float(s[7]) if s[7] > -1 else 0.0,
                "AR100": float(s[8]) if s[8] > -1 else 0.0,
                "prediction_count": len(preds),
            }
    except Exception as e:
        sys.stderr.write(f"Error during evaluation: {e}\n")

    # ALWAYS print valid JSON to stdout, even if an error occurred above
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()