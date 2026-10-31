# ViSC-Bench

**Vine Instance Segmentation under Corruption**

ViSC-Bench is a benchmark for evaluating grape-instance detection/segmentation under image corruption. The repository provides the public dataset split, COCO-format submission contract, private evaluation workflow, and public leaderboard.

> **Current scoring configuration:** the checked-in `competition/config.yaml` selects COCO bounding-box AP (`iou_type: bbox`). Do not assume segmentation scores are being computed unless the organizers explicitly announce a switch to `iou_type: segm`.

## Competition status

- Task: grape-instance detection (current configuration)
- Evaluation: COCO AP averaged over IoU thresholds 0.50:0.95
- Secondary metrics: AP50, AP75, size-specific AP, and AR
- Submission policy: one leaderboard submission per team by default
- Test annotations: private; only organizers can access them
- Public leaderboard: [GitHub Pages](https://faranbutt.github.io/ViSC-Bench/)

Competition dates, eligibility, prizes, and contact details should be announced by the organizers through the official competition channel.

## Repository layout

```text
data/public/
  images/
    train/
    val/
    test/
  annotations/
    instances_train.json
    instances_val.json
    images_test.json
competition/
  config.yaml
  validate_submission.py
  evaluate.py
  update_leaderboard.py
  render_leaderboard.py
leaderboard/
  leaderboard.csv
  leaderboard.md
docs/
  index.html
.github/workflows/
  competition-ci.yml
  score_submission.yml
```

The public test metadata file `data/public/annotations/images_test.json` contains image IDs, filenames, dimensions, and categories, but no ground-truth annotations. The hidden test annotations must remain private.

## Getting started

Clone the repository and install the dependencies:

```bash
git clone https://github.com/faranbutt/ViSC-Bench.git
cd ViSC-Bench
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Use the public training and validation images with their corresponding COCO annotations to train and validate your model. Do not use private annotations or attempt to infer hidden labels.

## Submission format

Submit one UTF-8 JSON file containing a JSON array of COCO result records. Each record represents one predicted instance.

### Detection (current official configuration)

```json
[
  {
    "image_id": 243,
    "category_id": 1,
    "bbox": [120.0, 80.0, 90.0, 110.0],
    "score": 0.93
  }
]
```

Requirements:

- `image_id` must be an ID listed in `images_test.json`.
- `category_id` must be one of the category IDs in `images_test.json`.
- `bbox` uses COCO `[x, y, width, height]` coordinates in pixels, relative to the provided resized test image.
- `score` must be a finite confidence value between 0 and 1.
- Width and height must be positive; boxes must lie within the image.
- Multiple predictions for an image are allowed. An image with no predicted instances may have no records.
- The file must be a JSON array, not a wrapped object.

### Segmentation format (only if the organizers enable it)

For a segmentation competition, each result must include `segmentation` as a COCO polygon list or COCO RLE object:

```json
[
  {
    "image_id": 243,
    "category_id": 1,
    "segmentation": [[120.0, 80.0, 210.0, 80.0, 210.0, 190.0, 120.0, 190.0]],
    "score": 0.93
  }
]
```

The active task is controlled by `competition/config.yaml`. Participants should follow the announced task and the sample submission distributed for that task.

## Local submission validation

Before uploading, validate the JSON structure and public image/category IDs:

```bash
python competition/validate_submission.py \
  path/to/predictions.json \
  data/public/annotations/images_test.json
```

The validator reads the active `iou_type` from `competition/config.yaml`. A successful validation only confirms format and public metadata consistency; it does not guarantee a high score.

## How submissions are scored

1. The organizer's submission form sends a dispatch event containing the team metadata and uploaded prediction's Google Drive file ID.
2. GitHub Actions downloads the prediction and the private ground truth.
3. The validator checks the prediction format and allowed public test IDs.
4. `competition/evaluate.py` runs the official `pycocotools` evaluator.
5. The leaderboard updater validates the metric JSON and applies the one-submission-per-team rule.
6. The leaderboard is rendered into static files and committed to the repository.

The public workflow must never upload, print, commit, or publish hidden annotations or raw participant file IDs.

## Metrics

The primary metric is COCO AP (mean average precision over IoU thresholds 0.50:0.95). The leaderboard also displays AP50 and AP75. The evaluator records AP by object size and average recall (AR1, AR10, AR100) for auditability.

A score of zero is a valid possible result, but an unexpected all-zero result should be investigated by the organizers. Check the hidden/public image ID and category alignment, prediction coordinates, and evaluation logs before accepting it as a meaningful score.

## Reproducibility and integrity

- Keep the official evaluation code and configuration version-controlled.
- Run the synthetic regression tests on every pull request.
- Keep hidden annotations and private image mappings outside the public repository.
- Do not modify the test set or scoring rules after submissions open without a public versioned announcement.
- Record the exact evaluation-code revision used for each official competition round.
- Publish clarifications and corrections transparently.

## For organizers

See [Organizer Guide](docs/ORGANIZER_GUIDE.md) for secrets, dispatch payload requirements, GitHub Pages setup, operational checks, and the pre-launch checklist.

## License and dataset attribution

Follow the license and attribution requirements of the source dataset and any separately distributed assets. The competition organizers should ensure that the applicable dataset license permits the intended redistribution and competition use.


## Google Forms submission integration

The Google Apps Script bridge is provided in [integrations/google-apps-script/Code.gs](integrations/google-apps-script/Code.gs). Bind it to the Google Form response spreadsheet, configure the required Apps Script properties, install the spreadsheet form-submit trigger, and deploy its callback web app. The bridge creates a private `ViSC_Submissions` tracking tab, dispatches submissions to GitHub Actions, and receives scoring status and headline metrics.

Configure these GitHub Actions secrets for status callbacks:

- `GOOGLE_SHEETS_CALLBACK_URL`
- `GOOGLE_SHEETS_CALLBACK_TOKEN`

The matching Apps Script project property is `CALLBACK_TOKEN`. The bridge also requires `GITHUB_OWNER`, `GITHUB_REPO`, and `GITHUB_TOKEN` Script Properties.

**Participant file privacy:** the current evaluator downloads prediction files with `gdown`, which requires link-view access. The Apps Script bridge checks that a submitted prediction file already has this permission; it does not change file sharing automatically. Disclose this to participants before launch. For private prediction files, replace `gdown` with authenticated Google Drive API access before accepting real submissions. Keep the response spreadsheet restricted to organizers.


### Current Google Form field mapping

The Apps Script field labels are configured to match the organizer-provided form:

| Google Form question title | Handling |
|---|---|
| `Team Name` | Required; used for duplicate-team enforcement |
| `Email` | Required; stored privately in the tracking sheet |
| `Team Leader` | Required; stored privately in the tracking sheet |
| `Model Name` | Optional; displayed on the public leaderboard |
| `Prediction File` | Required Google Drive file upload |

The script defaults `author_type` to `human` and `notes` to an empty value because those questions were not included in the supplied form-field list. The active policy is one submission per team. A repeated team name is rejected case-insensitively, including after a previous submission has failed; organizers must resolve or explicitly reset a team's record rather than silently allowing another attempt.

No live Google Form or response spreadsheet URL was supplied, so the Apps Script cannot be attached to the actual Google account or its trigger deployed from this repository. Follow the setup steps in the Organizer Guide after opening the linked response spreadsheet.
