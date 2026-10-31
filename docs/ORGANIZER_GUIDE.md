# ViSC-Bench Organizer Guide

This document is for benchmark organizers. Do not publish private ground truth, private image mappings, access tokens, or participant contact information.

## 1. Required GitHub configuration

In repository settings, confirm:

- The default branch is `main`.
- GitHub Actions are enabled.
- The workflow token has permission to write repository contents.
- GitHub Pages is configured to deploy from the `docs/` directory on `main` (branch deployment).
- The `competition-ci.yml` checks pass before changes are merged.

Create this repository Actions secret:

| Secret | Value |
|---|---|
| `HIDDEN_ANNOTATIONS_FILE_ID` | Google Drive file ID for the hidden COCO test annotations |

The current workflow uses `gdown` with a Drive file ID. The Drive file must be downloadable by the GitHub-hosted runner. Treat the ID as a credential: anyone who obtains an "anyone with the link" URL can download that file. For a high-stakes or long-running competition, migrate the hidden ground truth to private object storage or authenticated Google Drive API access using a dedicated service account. Never commit the hidden JSON to this repository.

## 2. Submission dispatch contract

The scoring workflow listens for the `repository_dispatch` event type `form_submission`.

The `client_payload` must contain:

```json
{
  "event_type": "form_submission",
  "client_payload": {
    "file_id": "GOOGLE_DRIVE_FILE_ID",
    "metadata": {
      "team": "Example Team",
      "run_id": "run_01",
      "author_type": "human",
      "model": "Model name",
      "notes": "Optional short description"
    }
  }
}
```

Important:

- `file_id` is the Google Drive file ID of the participant's prediction JSON, not a local path.
- `metadata` must be a JSON object.
- `team` is required and must be a printable name of at most 80 characters.
- The other metadata fields are optional; the workflow uses defaults where appropriate.
- The active configuration currently permits one leaderboard entry per team.
- Do not put participant file IDs, emails, API tokens, or private details in `metadata.notes`.

A dispatch can be sent with the GitHub REST API using a token that has permission to dispatch repository events. Keep that token in the form backend's secret manager, never in browser JavaScript.

## 3. End-to-end scoring process

The official workflow performs these operations:

1. Checks out `main` and installs Python dependencies from `requirements.txt`.
2. Parses and validates the dispatch metadata.
3. Downloads the hidden ground truth and submitted prediction JSON.
4. Validates predictions against public test image IDs and categories.
5. Runs `competition/evaluate.py` with the configured COCO IoU type.
6. Writes metrics JSON explicitly to `submissions/temp/metrics.json`.
7. Rejects duplicate teams and updates the leaderboard CSV atomically.
8. Regenerates the Markdown and static HTML leaderboard.
9. Commits the public leaderboard files.
10. Removes temporary prediction and hidden annotation files, including on failure.

Submissions are serialized with a workflow concurrency group so two jobs cannot race while updating the same CSV.

## 4. Required repository secrets and permissions

- `HIDDEN_ANNOTATIONS_FILE_ID`: required by the scoring workflow.
- The repository Actions token must be allowed to push commits to `main`; branch protection rules must permit the GitHub Actions bot or the workflow must be changed to open a pull request instead.
- The external form backend needs a separate token with the minimum permissions needed to create `repository_dispatch` events.

Never give participants write access to the organizer repository or its Actions secrets.

## 5. Test before launch

Run locally:

```bash
python -m pip install -r requirements.txt
python -m compileall -q competition tests
python -m unittest discover -s tests -v
```

Then verify all of the following with an organizer-only test submission:

- The hidden annotation file downloads and parses.
- Hidden image IDs and category IDs match the public test metadata.
- The test prediction file passes validation.
- A synthetic perfect prediction obtains AP close to 1.0 on the synthetic regression fixture.
- The real test submission produces plausible metrics when expected.
- The leaderboard CSV contains the expected row and correct metrics.
- The published GitHub Pages leaderboard displays the same row.
- No private files or raw Google Drive IDs are committed.

Do not treat an all-zero score as automatically valid. Investigate image ID alignment, category mapping, box coordinate convention, image resizing, and model output before publishing the result.

## 6. Changing the task

The active task is defined by `competition/config.yaml`.

Current official configuration:

```yaml
task: detection
iou_type: bbox
metric: coco_ap
one_submission_per_team: true
```

If changing to segmentation:

- Announce the change and effective date before accepting segmentation submissions.
- Set `iou_type: segm`.
- Distribute an updated segmentation-specific sample submission.
- Verify that the hidden ground truth contains valid COCO segmentation masks.
- Add a synthetic segmentation regression test.
- Run an end-to-end organizer test before launch.

Do not mix bbox AP and segmentation AP in the same leaderboard.

## 7. Leaderboard and audit trail

The public leaderboard is generated from `leaderboard/leaderboard.csv`. The renderer produces:

- `leaderboard/leaderboard.md`
- `docs/index.html`

The leaderboard stores a non-sensitive submission reference rather than the raw Drive file ID. Keep the CSV as the canonical public score record.

For a formal benchmark, also preserve an organizer-only audit record containing the submission event ID, evaluation commit SHA, configuration, and timestamp. Keep that record private and do not put private identifiers into the public CSV.

## 8. Pre-launch checklist

- [ ] Competition task and metric are publicly announced.
- [ ] Dataset license and redistribution permissions are confirmed.
- [ ] Public train/validation/test splits are frozen and documented.
- [ ] Hidden annotations are stored outside the public repository.
- [ ] GitHub Actions secret is configured and tested.
- [ ] External form backend token is stored server-side.
- [ ] Test submission validates and evaluates successfully.
- [ ] Duplicate team submission is rejected.
- [ ] CI passes on the default branch.
- [ ] GitHub Pages leaderboard is live and displays the empty state correctly.
- [ ] Submission deadlines, eligibility, appeals, and contact details are published.
