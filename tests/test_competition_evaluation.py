import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from competition.evaluate import evaluate


class CompetitionEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.gt_path = self.root / "ground_truth.json"
        self.pred_path = self.root / "predictions.json"
        ground_truth = {
            "info": {},
            "licenses": [],
            "images": [{"id": 1, "file_name": "image.jpg", "width": 100, "height": 100}],
            "categories": [{"id": 1, "name": "grape"}],
            "annotations": [{
                "id": 1, "image_id": 1, "category_id": 1,
                "bbox": [10, 10, 30, 30], "area": 900, "iscrowd": 0
            }],
        }
        prediction = [{
            "image_id": 1, "category_id": 1,
            "bbox": [10, 10, 30, 30], "score": 0.99
        }]
        self.gt_path.write_text(json.dumps(ground_truth), encoding="utf-8")
        self.pred_path.write_text(json.dumps(prediction), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_perfect_bbox_prediction_has_perfect_ap(self):
        metrics = evaluate(self.gt_path, self.pred_path, "bbox")
        self.assertEqual(metrics["prediction_count"], 1)
        self.assertAlmostEqual(metrics["AP"], 1.0, places=5)
        self.assertAlmostEqual(metrics["AP50"], 1.0, places=5)
        self.assertAlmostEqual(metrics["AP75"], 1.0, places=5)

    def test_empty_predictions_return_valid_zero_metrics(self):
        self.pred_path.write_text("[]", encoding="utf-8")
        metrics = evaluate(self.gt_path, self.pred_path, "bbox")
        self.assertEqual(metrics["prediction_count"], 0)
        self.assertEqual(metrics["AP"], 0.0)


if __name__ == "__main__":
    unittest.main()
