# Secure Download Route Verification – Issue Report (2025-12-21)

## Summary
- Implemented a secure attachment download route in app/routes/files.py and linked it from guest/student notice pages.
- Server runs and the home page responds (HTTP 200), but requests to /files/notice/<id> return HTTP 500.
- The issue appears when calling non-existent file IDs (e.g., 1, 9999) before any test attachment exists.

## Environment
- OS: Windows (PowerShell shell)
- Python: 3.11.9 (venv activated)
- App: Flask dev server via run.py
- Notable warning: FutureWarning about deprecated google.generativeai package (informational only).

## Changes Involved
- Secure route: [app/routes/files.py](app/routes/files.py)
- Guest page links: [app/templates/guest/notice_detail.html](app/templates/guest/notice_detail.html)
- Student detail page: [app/templates/student/notice_detail.html](app/templates/student/notice_detail.html)
- Student route for detail: [app/routes/student.py](app/routes/student.py)
- Blueprint registration: [app/__init__.py](app/__init__.py)

## Reproduction Steps
1. Activate venv and start server:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& d:\mn\campus-management-assistant\venv\Scripts\Activate.ps1
& d:\mn\campus-management-assistant\venv\Scripts\python.exe d:\mn\campus-management-assistant\run.py
```
2. Verify home responds:
```powershell
Invoke-WebRequest -Uri http://localhost:5000/ -Method GET
# Observed: 200
```
3. Hit secure download route with a sample ID:
```powershell
Invoke-WebRequest -Uri http://localhost:5000/files/notice/1 -Method GET -ErrorAction SilentlyContinue
Invoke-WebRequest -Uri http://localhost:5000/files/notice/9999 -Method GET -ErrorAction SilentlyContinue
# Observed: 500 Internal Server Error
```

## Expected vs Actual
- Expected: 404 Not Found for non-existent file IDs; 403 Forbidden when user lacks access; 200 OK with a valid file and allowed visibility.
- Actual: 500 Internal Server Error for tested IDs, even when no file record should exist.

## Route Logic (Intended Behavior)
- Loads `NoticeFile` by `file_id` and checks parent `Notice` is `published`.
- Visibility:
  - public → accessible to everyone
  - student/restricted → requires authenticated `student`
- Serves via `send_from_directory`, ensures path is under uploads, returns 404 if missing on disk.
- Logs failures to `system_logs` and preserves 404/403 statuses raised via `abort()`.

## Initial Hypotheses
- No file record exists yet; an exception is thrown before returning 404 (e.g., ORM call or relationship access behavior in this environment).
- SQLAlchemy version differences: `query.get()` may be deprecated or misbehaving; however, the code attempts to handle non-existent IDs by short-circuiting before dereferencing.
- A hidden error occurs in import side-effects or request handling; full stack traces are needed to confirm.

## Next Investigation Steps (Non-breaking)
- Enable Flask debug temporarily to capture full stack traces for /files/notice/<id>.
- Create a test notice, upload an attachment via the UI, publish, and test using a real `file_id`.
- Confirm SQLAlchemy version and adjust the retrieval method (e.g., `db.session.get(...)`) if needed, keeping changes minimal.
- Inspect `system_logs` for entries from the files module.

## Current Status
- Server active; home returns 200.
- Secure download route implemented and registered; UI links updated.
- Verification blocked by 500 without a stack trace; likely resolves once a real attachment exists and/or after capturing error detail.

## Observed Terminal Session (2025-12-21)

### Summary of outcomes
- venv activation succeeded.
- Home page `GET /` returned 200 OK with guest links.
- Secure download route `GET /files/notice/1` returned 500 Internal Server Error.

### Commands and output

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& d:\mn\campus-management-assistant\venv\Scripts\Activate.ps1

# Home route check
Invoke-WebRequest -Uri http://localhost:5000/ -Method GET

StatusCode        : 200
StatusDescription : OK
Content           : <!doctype html>
                    <html lang="en">
                      <head>
                        <meta charset="utf-8">
                        <meta name="viewport"
                    content="width=device-width, initial-scale=1">
                        <title>Campus Management Assistant</title>
                        <link r...
RawContent        : HTTP/1.1 200 OK
                    Vary: Cookie
                    Connection: close
                    Content-Length: 1107
                    Content-Type: text/html; charset=utf-8
                    Date: Sun, 21 Dec 2025 12:36:48 GMT
                    Server: Werkzeug/3.1.4 Python/3.11.9

Links             : Login (/auth/login), Register (/auth/register),
                    View Public Notices (/notices), Open Chatbot (/chatbot)

# Secure download route check (sample id)
Invoke-WebRequest -Uri http://localhost:5000/files/notice/1 -Method GET -ErrorAction SilentlyContinue

Invoke-WebRequest : Internal Server Error
The server encountered an internal error and was unable to complete
your request. Either the server is overloaded or there is an error in
the application.
```

### Notes
- The 500 error on `/files/notice/1` likely reflects a missing file record or disk file; with a valid `file_id` from a published notice attachment, the route should return 200 or 403/404 appropriately.
- Capturing a stack trace (temporary debug) or testing with a real uploaded attachment will help confirm the route behavior.
