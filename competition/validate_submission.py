import json
import sys
from pathlib import Path

import yaml


def main(pred_path, images_test_path):
    cfg = yaml.safe_load(open("competition/config.yaml", encoding="utf-8"))
    iou_type = cfg.get("iou_type", "bbox")

    preds = json.loads(Path(pred_path).read_text(encoding="utf-8"))
    meta = json.loads(Path(images_test_path).read_text(encoding="utf-8"))

    if not isinstance(preds, list):
        raise SystemExit("Error: submission must be a JSON array of COCO prediction records.")
    if not preds:
        raise SystemExit("Error: submission is empty.")

    allowed_image_ids = {int(x["id"]) for x in meta["images"]}
    allowed_category_ids = {int(c["id"]) for c in meta["categories"]}

    for i, pred in enumerate(preds):
        if not isinstance(pred, dict):
            raise SystemExit(f"Error: row {i} is not an object.")

        required = {"image_id", "category_id", "score"}
        required |= {"bbox"} if iou_type == "bbox" else {"segmentation"}
        missing = required - set(pred)
        if missing:
            raise SystemExit(f"Error: row {i} missing fields: {sorted(missing)}")

        if int(pred["image_id"]) not in allowed_image_ids:
            raise SystemExit(f"Error: row {i} has unknown image_id={pred['image_id']}")
        if int(pred["category_id"]) not in allowed_category_ids:
            raise SystemExit(f"Error: row {i} has unknown category_id={pred['category_id']}")

        score = float(pred["score"])
        if not (0.0 <= score <= 1.0):
            raise SystemExit(f"Error: row {i} score must be in [0,1].")

        if iou_type == "bbox":
            bbox = pred["bbox"]
            if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
                raise SystemExit(f"Error: row {i} bbox must be [x,y,w,h].")
            if float(bbox[2]) <= 0 or float(bbox[3]) <= 0:
                raise SystemExit(f"Error: row {i} bbox width/height must be positive.")
        else:
            seg = pred["segmentation"]
            if not isinstance(seg, (list, dict)) or not seg:
                raise SystemExit(f"Error: row {i} segmentation must be non-empty list or RLE dict.")

    print("Validation Successful")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: validate_submission.py <predictions.json> <images_test.json>")
    main(sys.argv[1], sys.argv[2])