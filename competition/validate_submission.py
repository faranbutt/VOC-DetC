import json
import math
import sys
from pathlib import Path

import yaml


def finite_number(value, label: str, row: int) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise SystemExit(f"Error: row {row} {label} must be numeric.")
    if not math.isfinite(number):
        raise SystemExit(f"Error: row {row} {label} must be finite.")
    return number


def main(pred_path: str, images_test_path: str) -> None:
    config = yaml.safe_load(Path("competition/config.yaml").read_text(encoding="utf-8")) or {}
    iou_type = config.get("iou_type", "bbox")
    if iou_type not in ("bbox", "segm"):
        raise SystemExit(f"Unsupported iou_type in competition/config.yaml: {iou_type}")

    try:
        predictions = json.loads(Path(pred_path).read_text(encoding="utf-8"))
        test_metadata = json.loads(Path(images_test_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read submission or test metadata JSON: {exc}")

    if not isinstance(predictions, list):
        raise SystemExit("Submission must be a JSON array of COCO prediction records.")
    if not predictions:
        raise SystemExit("Submission is empty.")
    if not isinstance(test_metadata, dict):
        raise SystemExit("Test metadata must be a COCO JSON object.")

    images = {int(image["id"]): image for image in test_metadata.get("images", [])}
    categories = {int(category["id"]) for category in test_metadata.get("categories", [])}
    if not images or not categories:
        raise SystemExit("Test metadata must contain images and categories.")

    for index, prediction in enumerate(predictions):
        if not isinstance(prediction, dict):
            raise SystemExit(f"Error: row {index} is not an object.")

        required = {"image_id", "category_id", "score"}
        required.add("bbox" if iou_type == "bbox" else "segmentation")
        missing = required - prediction.keys()
        if missing:
            raise SystemExit(f"Error: row {index} missing fields: {sorted(missing)}")

        try:
            image_id = int(prediction["image_id"])
            category_id = int(prediction["category_id"])
        except (TypeError, ValueError):
            raise SystemExit(f"Error: row {index} image_id and category_id must be integers.")

        if image_id not in images:
            raise SystemExit(f"Error: row {index} has unknown image_id={image_id}.")
        if category_id not in categories:
            raise SystemExit(f"Error: row {index} has unknown category_id={category_id}.")

        score = finite_number(prediction["score"], "score", index)
        if not 0.0 <= score <= 1.0:
            raise SystemExit(f"Error: row {index} score must be in [0, 1].")

        if iou_type == "bbox":
            bbox = prediction["bbox"]
            if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
                raise SystemExit(f"Error: row {index} bbox must be [x, y, width, height].")
            x, y, width, height = [
                finite_number(value, "bbox coordinate", index) for value in bbox
            ]
            if width <= 0 or height <= 0:
                raise SystemExit(f"Error: row {index} bbox width and height must be positive.")
            image = images[image_id]
            if x < 0 or y < 0 or x + width > int(image["width"]) + 1 or y + height > int(image["height"]) + 1:
                raise SystemExit(f"Error: row {index} bbox lies outside image {image_id}.")
        else:
            segmentation = prediction["segmentation"]
            if not isinstance(segmentation, (list, dict)) or not segmentation:
                raise SystemExit(f"Error: row {index} segmentation must be non-empty polygons or RLE.")
            if isinstance(segmentation, dict) and not {"size", "counts"}.issubset(segmentation):
                raise SystemExit(f"Error: row {index} RLE segmentation requires size and counts.")

    print(f"Validation successful: {len(predictions)} predictions across {len(images)} test images.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python competition/validate_submission.py <predictions.json> <images_test.json>")
    main(sys.argv[1], sys.argv[2])
