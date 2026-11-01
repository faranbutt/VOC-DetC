# VOC-DeTC

**VOC Object Detection under Corruption**

VOC-DeTC is an wine-detection benchmark for evaluating how well models detect wine grapes in images affected by corruption. Participants submit predicted bounding boxes and confidence scores in COCO results JSON format. Submissions are evaluated automatically against the private test annotations.

## Public data

The public dataset is organized as follows:

```text
data/public/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── annotations/
    ├── instances_train.json
    ├── instances_val.json
    └── images_test.json
```

- `images/train/`: training images.
- `images/val/`: validation images.
- `images/test/`: test images used to generate predictions.
- `instances_train.json`: COCO-format training annotations.
- `instances_val.json`: COCO-format validation annotations.
- `images_test.json`: test-image metadata and category definitions.

**The test annotations are hidden.** `images_test.json` intentionally contains image metadata and categories but has an empty `annotations` array. Use its image IDs and category IDs when creating your submission. Do not add or infer ground-truth annotations.

## Task: object detection

Submit one prediction record for each detected object. Each record must contain:

| Field | Description |
|---|---|
| `image_id` | Integer image ID from `images_test.json`. |
| `category_id` | Integer category ID from the `categories` section of `images_test.json`. |
| `bbox` | Bounding box in COCO `[x, y, width, height]` format, in pixels. |
| `score` | Confidence score between `0` and `1`. |

Coordinates must refer to the provided test images at their published resolution. The bounding-box format is **`[x, y, width, height]`**, not `[x1, y1, x2, y2]` and not normalized YOLO coordinates.

## Submission format

Upload a `.json` file containing a JSON array of COCO detection records. For example:

```json
[
  {
    "image_id": 301,
    "category_id": 1,
    "bbox": [120.0, 80.0, 90.0, 110.0],
    "score": 0.93
  },
  {
    "image_id": 301,
    "category_id": 2,
    "bbox": [340.0, 125.0, 75.0, 96.0],
    "score": 0.87
  }
]
```

The values above are illustrative. Replace them with valid image and category IDs from your downloaded public metadata and coordinates from the corresponding test image.

### Submission requirements

1. The file must be valid JSON and its top-level value must be an array (`[]` is valid JSON, but an empty submission may be rejected).
2. Every prediction must include `image_id`, `category_id`, `bbox`, and `score`.
3. Use only image IDs and category IDs listed in `images_test.json`.
4. `bbox` must contain four finite numeric values: `[x, y, width, height]`.
5. Width and height must be positive. Boxes must lie within the corresponding image boundaries.
6. `score` must be a finite number in the range `[0, 1]`.
7. Submit predictions only. Do not include ground-truth annotations, image files, training labels, or explanatory text in the JSON file.
8. An image with no detections does not need a prediction record.

See `data/public/annotations/submission_format.json` and `sample_submission.json` if they are provided in the repository; use the repository files as the final authority for the accepted schema.

## How to submit

Submit your prediction JSON file through the official Google Form:

[Open the VOC-DeTC submission form](https://docs.google.com/forms/d/e/1FAIpQLSfR0vFHvkZT-qMUHREBfsOMJyeZCzhfPJ_omtaEPvWJyUGLHw/viewform)

Complete the form's required team and model information and upload or provide the prediction file as requested. Please do not submit private ground-truth data or share private organizer links.

## Evaluation and leaderboard

Submissions are checked for format and valid IDs, then evaluated against the private test annotations using COCO bounding-box evaluation. The leaderboard reports detection metrics such as AP, AP50, and AP75. A successful format validation does not guarantee a high detection score; the score measures agreement between your predictions and the hidden annotations.

[View the VOC-DeTC leaderboard](https://faranbutt.github.io/VOC-DetC/)

## Reproducibility and fair use

- Use the publicly released training and validation data for model development.
- Use the published test images and metadata to prepare predictions.
- Do not attempt to obtain, reconstruct, publish, or otherwise use hidden test annotations.
- Report the model and inference settings accurately in the submission form.
- Do not include Google Drive file IDs, private download URLs, credentials, or organizer-only materials in public issues, pull requests, or leaderboard metadata.

## Questions and troubleshooting

Before submitting, verify that your JSON parses, every ID exists in `images_test.json`, all boxes use pixel-based COCO `xywh` coordinates, and every confidence score is between `0` and `1`.