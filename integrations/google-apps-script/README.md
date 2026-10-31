# Google Forms → Sheets → GitHub Actions integration

This bridge processes **new** Google Form submissions while preserving the existing Form response tab.

## Important: existing response history

1. Bind the Apps Script project to the existing response spreadsheet.
2. Paste the current `Code.gs` from this repository into the bound Apps Script project.
3. Run `setupSubmissionsSheet()` manually once and authorize the requested Google permissions.
4. Confirm that a separate `ViSC_Submissions` tab has been created and contains historical rows marked `HISTORICAL_NOT_SCORED`.
5. Confirm the original Form response tab and its existing rows are unchanged.
6. Only then install the spreadsheet's **On form submit** trigger for `onFormSubmit`.

The migration is resumable: it records the original response row number and skips rows already imported. It does not dispatch historical responses for scoring. Do not delete the `HISTORICAL_IMPORT_DONE` Script Property unless you intentionally plan and understand a migration reset.

The setup function identifies the response tab from the exact column headers. Required headers are `Team Name`, `Email`, `Team Leader`, and `Prediction File`. Optional columns are `Model Name`, `Author Type`, and `Notes`.

## Apps Script properties

In **Project Settings → Script Properties**, add:

- `GITHUB_OWNER`: `faranbutt`
- `GITHUB_REPO`: `ViSC-Bench`
- `GITHUB_TOKEN`: fine-grained GitHub token with minimum repository access and permission to create repository dispatch events
- `CALLBACK_TOKEN`: long random secret shared with the GitHub Actions callback secret

Never commit tokens or callback URLs containing secrets.

## Install the callback endpoint

1. In Apps Script, deploy the project as a **Web app**.
2. Set **Execute as** to the spreadsheet owner.
3. Set access to the broadest option needed for GitHub Actions to reach the endpoint.
4. Copy the deployed `/exec` URL.
5. Add GitHub repository Actions secrets:
   - `GOOGLE_SHEETS_CALLBACK_URL`: deployed web app URL
   - `GOOGLE_SHEETS_CALLBACK_TOKEN`: same value as Apps Script `CALLBACK_TOKEN`

The callback checks the shared token before updating the tracking tab.

## GitHub Actions secrets

Also configure:

- `HIDDEN_ANNOTATIONS_FILE_ID`: Drive file ID for the private ground-truth JSON

The scoring workflow currently uses `gdown` for participant prediction downloads. Therefore participant prediction files must be readable by anyone with the link. The Apps Script does not change sharing permissions; it rejects a file that is not already link-viewable. This is a privacy trade-off. For confidential submissions, replace this with authenticated Google Drive API access rather than asking participants to expose files by link.

## Form field names

The current mapping is case-sensitive and must match the Google Form question titles:

- `Team Name`
- `Email`
- `Team Leader`
- `Model Name`
- `Prediction File`

The code defaults `Author Type` to `human` and `Notes` to empty when those optional questions are absent.

## Before opening the competition

- Verify the historical import count against the number of non-empty existing response rows.
- Submit one organizer-controlled test form response using a test team and test prediction file.
- Verify that it appears as `QUEUED` in `ViSC_Submissions`.
- Verify the GitHub Actions run and the callback status/metrics.
- Test a second submission using the same team name; it should be recorded as `REJECTED_DUPLICATE`.
- Confirm the public leaderboard contains no emails, Drive IDs, or hidden annotations.

**Do not use real participant submissions until the workflow has been tested end-to-end.**
