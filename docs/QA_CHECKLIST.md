# QA Checklist

Use this checklist before hosted deployment or packaging work. Keep the API in local-first mode unless a test explicitly says otherwise.

## Automated Smoke

1. Install dependencies and browsers:
   ```powershell
   npm install
   cd apps\web
   npx playwright install chromium
   ```
2. Run the browser smoke suite:
   ```powershell
   npm run qa:e2e
   ```
3. Run the normal validation set:
   ```powershell
   npm run build:web
   npm run check:garden-assets
   cd apps\api
   .\.venv\Scripts\python.exe -m unittest discover -s tests
   ```

## Demo State

1. Seed a visual QA database:
   ```powershell
   npm run seed:demo -- --reset
   ```
2. Start the API against the printed demo database URL.
3. Start the web app with `npm run dev:web:host`.
4. Inspect Capture, Inbox, Tasks, Projects, Garden, Recaps, and Settings.

## First Launch

1. Start the app from a clean local database.
2. Confirm the top navigation only shows Capture, Inbox, Tasks, Projects, Garden, Recaps, and Settings.
3. Confirm Settings loads without a permanent loading state.
4. Confirm Garden loads without a permanent loading state.

## Provider Setup

1. Open Settings.
2. Confirm extraction provider, extraction model, recap provider, recap model, STT provider, and STT model are visible.
3. Run extraction, narrative, and STT checks.
4. Confirm failures are actionable and do not imply silent fallback.

## Voice Capture

1. Open Capture.
2. Click the centered mic control.
3. Confirm recording state and audio activity are visible.
4. Stop recording with the same control.
5. Confirm transcription starts automatically.
6. Confirm the transcript appears in the composer and remains editable.
7. Confirm extraction starts automatically and task suggestions appear for review.
8. Confirm the audio preview is cleared after successful transcription.
9. If transcription fails, confirm retry remains possible and the temporary recording is not discarded first.

## Transcript Review And Extraction

1. Save a typed note or finish a voice recording.
2. Confirm typed notes run extraction on submit and voice transcripts run extraction automatically.
3. Confirm suggested tasks appear in Review.
4. Edit one candidate and reject one candidate if available.
5. Confirm selected tasks.
6. Confirm accepted tasks appear in Inbox and rejected tasks do not.

## Inbox Manual Quick Add

1. Open Inbox.
2. Expand Add manually.
3. Create a task with title, project, status, due date, priority, effort, and energy.
4. Confirm the task appears immediately.

## Tasks Filters

1. Open Tasks.
2. Test Date filters: All active, Today, This week, Overdue, Completed.
3. Confirm completed tasks do not appear in All active.
4. Confirm completed tasks appear in Completed.
5. Test Status filter with inbox, planned, in progress, blocked, completed, and archived.
6. Test Project filter with at least two projects and unassigned tasks.

## Projects

1. Create a project.
2. Edit its name and description.
3. Delete a project while keeping associated tasks.
4. Confirm those tasks remain and become unassigned.
5. Delete a project and its associated tasks.
6. Confirm those tasks disappear from task lists.

## Garden

1. Open Garden with no tasks and confirm no harsh decay state.
2. Complete tasks and recompute.
3. Confirm progress/restoration is visible.
4. Add overdue active tasks and recompute.
5. Confirm disrepair is visible but still readable and recoverable.

## Recaps

1. Open Recaps.
2. Generate weekly, monthly, and yearly recaps.
3. Confirm compact metrics, highlights, streak values, and the optional reflection render.
4. Confirm empty or low-activity recaps feel intentional, not broken.

## Settings And Sync Readiness

1. Open Settings.
2. Confirm local-first defaults are visible.
3. Register a device if needed.
4. Confirm sync status remains optional and does not block normal use.

## Hosted Mode Smoke

1. Start Docker Desktop.
2. Run:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\hosted-rehearsal.ps1 -Reset
   ```
3. Confirm the script reports `health: ok`, `unauthorized_write_status: 401`, and `pushed_change_count: 1`.
4. Confirm CORS preflight from the hosted frontend origin:
   ```powershell
   curl.exe -i -X OPTIONS "http://127.0.0.1:18080/entries" -H "Origin: http://127.0.0.1:15174" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type,authorization"
   ```
5. Confirm a hosted frontend build works with:
   ```powershell
   $env:VITE_API_BASE_URL="http://127.0.0.1:18080"
   $env:VITE_API_AUTH_TOKEN="replace-with-a-long-random-token"
   npm run build:web
   ```
6. Confirm local mode still works without hosted env vars after the compose stack is stopped.
