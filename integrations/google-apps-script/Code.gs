/**
 * ViSC-Bench Google Forms -> Sheets/Drive -> GitHub Actions bridge.
 *
 * Bind this Apps Script project to the Google Sheets response spreadsheet.
 * Configure Script Properties as described in integrations/google-apps-script/README.md.
 *
 * IMPORTANT: Set the field labels below to match the exact Google Form question titles.
 */

const VISC = {
  // Exact Google Form question titles (case-sensitive).
  fields: {
    team: "Team Name",
    email: "Contact Email",
    leader: "Team Leader",
    model: "Model Name",
    authorType: "Author Type",
    notes: "Notes",
    predictionFile: "Prediction JSON File"
  },
  submissionsSheet: "ViSC_Submissions",
  headers: [
    "submission_id", "submitted_at_utc", "team", "contact_email",
    "team_leader", "model", "author_type", "notes", "drive_file_id",
    "status", "github_run_id", "AP", "AP50", "AP75", "error_message"
  ]
};

/**
 * Install this as an installable "On form submit" trigger on the response spreadsheet.
 */
function onFormSubmit(e) {
  if (!e || !e.namedValues) {
    throw new Error("This function must be run by the spreadsheet form-submit trigger.");
  }

  const props = PropertiesService.getScriptProperties();
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);

  let sheet;
  let rowNumber;
  let submissionId;
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    sheet = getOrCreateSubmissionsSheet_(ss);
    const values = e.namedValues;

    const team = requiredField_(values, VISC.fields.team);
    const email = requiredField_(values, VISC.fields.email);
    const leader = requiredField_(values, VISC.fields.leader);
    const model = optionalField_(values, VISC.fields.model);
    const authorType = optionalField_(values, VISC.fields.authorType) || "human";
    const notes = optionalField_(values, VISC.fields.notes);
    const fileId = extractDriveFileId_(requiredField_(values, VISC.fields.predictionFile));

    if (team.length > 80) throw new Error("Team name must be 80 characters or fewer.");
    if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      throw new Error("Please provide a valid contact email address.");
    }
    if (leader.length > 120 || model.length > 160 || notes.length > 500) {
      throw new Error("One or more fields exceed the allowed length.");
    }

    const existing = findTeamRow_(sheet, team);
    if (existing) {
      appendRecord_(sheet, [
        Utilities.getUuid(), new Date().toISOString(), team, email, leader,
        model, authorType, notes, fileId, "REJECTED_DUPLICATE", "", "", "", "",
        "A submission for this team has already been received."
      ]);
      return;
    }

    submissionId = Utilities.getUuid();
    rowNumber = appendRecord_(sheet, [
      submissionId, new Date().toISOString(), team, email, leader,
      model, authorType, notes, fileId, "RECEIVED", "", "", "", "", ""
    ]);

    // Ensure the Actions runner can download the prediction file with gdown.
    // This grants link-based read access to this prediction file only.
    const file = DriveApp.getFileById(fileId);
    file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

    const payload = {
      event_type: "form_submission",
      client_payload: {
        submission_id: submissionId,
        file_id: fileId,
        metadata: {
          team: team,
          contact_email: email,
          team_leader: leader,
          model: model || "unknown",
          author_type: authorType,
          notes: notes,
          run_id: "run_01"
        }
      }
    };

    dispatchToGitHub_(props, payload);
    sheet.getRange(rowNumber, 10).setValue("QUEUED");
  } catch (error) {
    if (sheet && rowNumber) {
      sheet.getRange(rowNumber, 10).setValue("DISPATCH_FAILED");
      sheet.getRange(rowNumber, 15).setValue(String(error.message || error));
    }
    throw error;
  } finally {
    lock.releaseLock();
  }
}

/**
 * GitHub Actions calls this endpoint after scoring, including on failures.
 * Deploy as a Web App that executes as the owner and is accessible to anyone.
 * The shared token is checked before touching the spreadsheet.
 */
function doPost(e) {
  try {
    const body = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    const expected = PropertiesService.getScriptProperties().getProperty("CALLBACK_TOKEN");
    if (!expected || !body.token || !constantTimeEquals_(String(body.token), expected)) {
      return jsonResponse_({ ok: false, error: "Unauthorized" });
    }
    if (!body.submission_id || !["SUCCESS", "FAILED", "CANCELLED"].includes(body.status)) {
      return jsonResponse_({ ok: false, error: "Invalid callback payload" });
    }

    const sheet = getOrCreateSubmissionsSheet_(SpreadsheetApp.getActiveSpreadsheet());
    const row = findSubmissionRow_(sheet, String(body.submission_id));
    if (!row) return jsonResponse_({ ok: false, error: "Submission not found" });

    const metrics = body.metrics || {};
    sheet.getRange(row, 10).setValue(body.status);
    sheet.getRange(row, 11).setValue(String(body.github_run_id || ""));
    sheet.getRange(row, 12, 1, 3).setValues([[
      finiteMetric_(metrics.AP), finiteMetric_(metrics.AP50), finiteMetric_(metrics.AP75)
    ]]);
    sheet.getRange(row, 15).setValue(String(body.error_message || "").slice(0, 500));
    return jsonResponse_({ ok: true });
  } catch (error) {
    return jsonResponse_({ ok: false, error: String(error.message || error) });
  }
}

function dispatchToGitHub_(props, payload) {
  const owner = requiredProperty_(props, "GITHUB_OWNER");
  const repo = requiredProperty_(props, "GITHUB_REPO");
  const token = requiredProperty_(props, "GITHUB_TOKEN");
  const url = "https://api.github.com/repos/" + encodeURIComponent(owner) +
    "/" + encodeURIComponent(repo) + "/dispatches";

  const response = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    headers: {
      Authorization: "Bearer " + token,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28"
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  const status = response.getResponseCode();
  if (status !== 204) {
    throw new Error("GitHub dispatch failed (HTTP " + status + "): " +
      response.getContentText().slice(0, 300));
  }
}

function getOrCreateSubmissionsSheet_(ss) {
  let sheet = ss.getSheetByName(VISC.submissionsSheet);
  if (!sheet) sheet = ss.insertSheet(VISC.submissionsSheet);
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, VISC.headers.length).setValues([VISC.headers]);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function appendRecord_(sheet, values) {
  sheet.appendRow(values);
  return sheet.getLastRow();
}

function findTeamRow_(sheet, team) {
  if (sheet.getLastRow() < 2) return null;
  const teams = sheet.getRange(2, 3, sheet.getLastRow() - 1, 1).getValues();
  const target = team.trim().toLocaleLowerCase();
  for (let i = 0; i < teams.length; i++) {
    if (String(teams[i][0]).trim().toLocaleLowerCase() === target) return i + 2;
  }
  return null;
}

function findSubmissionRow_(sheet, submissionId) {
  if (sheet.getLastRow() < 2) return null;
  const ids = sheet.getRange(2, 1, sheet.getLastRow() - 1, 1).getValues();
  for (let i = 0; i < ids.length; i++) {
    if (String(ids[i][0]) === submissionId) return i + 2;
  }
  return null;
}

function requiredField_(values, label) {
  const value = optionalField_(values, label);
  if (!value) throw new Error("Missing required Google Form field: " + label);
  return value;
}

function optionalField_(values, label) {
  const raw = values[label];
  if (raw === undefined || raw === null) return "";
  return String(Array.isArray(raw) ? raw[0] : raw).trim();
}

function extractDriveFileId_(value) {
  const match = String(value).match(/[-\w]{25,}/);
  if (!match) throw new Error("Could not extract a Google Drive file ID from the upload response.");
  return match[0];
}

function requiredProperty_(props, key) {
  const value = props.getProperty(key);
  if (!value) throw new Error("Missing Apps Script property: " + key);
  return value;
}

function finiteMetric_(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : "";
}

function constantTimeEquals_(a, b) {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return result === 0;
}

function jsonResponse_(value) {
  return ContentService.createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}

/** Run once manually to create the tracking tab before enabling the trigger. */
function setupSubmissionsSheet() {
  getOrCreateSubmissionsSheet_(SpreadsheetApp.getActiveSpreadsheet());
}
