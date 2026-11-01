# VOC-DeTC
VOC Object Detection under Corruption
## Public data

- `data/public/images/train/`
- `data/public/images/val/`
- `data/public/images/test/`
- `data/public/annotations/instances_train.json`
- `data/public/annotations/instances_val.json`
- `data/public/annotations/images_test.json`

`images_test.json` contains image metadata and categories only. It intentionally has an empty annotations list.

## Submission

Submit a JSON array of COCO prediction records.

Detection:

```json
[
  {"image_id": 301, "category_id": 1, "bbox": [120.0, 80.0, 90.0, 110.0], "score": 0.93}
]
```

## Form to Submit:
https://docs.google.com/forms/d/e/1FAIpQLSfR0vFHvkZT-qMUHREBfsOMJyeZCzhfPJ_omtaEPvWJyUGLHw/viewform