# Campus Management Assistant — Change Log and Problem Report

Date: 2025-12-21
Environment: Windows, Python 3.11 venv (avoid 3.12), VS Code

## Summary

This document records issues encountered and all changes implemented to stabilize and improve the Campus Management Assistant, with emphasis on the chatbot, moderator UI routing gaps, and consistent UI buttons.

## Problems Encountered

- Deprecated SDK warning: `google.generativeai` support ended; caused model compatibility errors.
- 400 errors from `/chatbot/query`: “Configured model is not available for this SDK/version.”
- Moderator “View” links 404: missing moderator-specific detail routes/templates.
- Chatbot UI looked like a plain form; lacked a proper chat window experience.
- Inconsistent text links across pages (guest/admin/auth); requested conversion to buttons.
- PowerShell execution policy blocked venv activation scripts; needed safe alternatives.
- Sample data lacking for 3rd-year exam queries; needed reasoning-rich content.

## Implemented Changes

### Chatbot Service and SDK

- Migrated service to use `google.genai` only; deprecated fallback removed.
  - File: [app/services/chatbot_service.py](../app/services/chatbot_service.py)
  - Configure client: `Client(api_key=GEMINI_API_KEY)`.
  - Generation call: `client.responses.generate(model=GEMINI_MODEL, input=prompt)`.
  - Parse: `response.output_text` with candidate fallback.
- Health endpoint now reports `sdk: google.genai`, readiness, and model.
  - Route: [app/routes/chatbot.py](../app/routes/chatbot.py)
  - Health logic: [app/services/chatbot_service.py](../app/services/chatbot_service.py)
- Enforced strict, context-only answers and multilingual reply behavior.
- Model config: Use `GEMINI_MODEL` from `.env`; default `gemini-1.5-flash`.
  - `.env` update: [./../.env](../.env)

### Chatbot UI/UX

- Student and guest chatbot pages redesigned to a proper chat window:
  - Scrollable message history, user/bot bubbles, header with status.
  - Typing indicator, Enter-to-send, fetch-based posting to `/chatbot/query`.
  - Files:
    - [app/templates/student/chatbot.html](../app/templates/student/chatbot.html)
    - [app/templates/guest/chatbot.html](../app/templates/guest/chatbot.html)
    - [app/static/css/chatbot.css](../app/static/css/chatbot.css)
    - [app/static/js/chatbot.js](../app/static/js/chatbot.js)

### Moderator Routing Gaps (READ-ONLY Detail Pages)

- Added moderator notice detail route and template (read-only):
  - Route: `/moderator/notices/<int:notice_id>`
  - Files:
    - [app/routes/moderator.py](../app/routes/moderator.py)
    - [app/templates/moderator/notice_detail.html](../app/templates/moderator/notice_detail.html)
- Added moderator FAQ detail route and template (read-only):
  - Route: `/moderator/faq/<int:faq_id>`
  - Files:
    - [app/routes/moderator.py](../app/routes/moderator.py)
    - [app/templates/moderator/faq_detail.html](../app/templates/moderator/faq_detail.html)
- Fixed “View” buttons in moderator lists to point to new routes:
  - Files:
    - [app/templates/moderator/notices.html](../app/templates/moderator/notices.html)
    - [app/templates/moderator/faq.html](../app/templates/moderator/faq.html)

### Consistent Buttons Across Pages

- Replaced plain text links with styled `btn` buttons:
  - Guest: [app/templates/guest/home.html](../app/templates/guest/home.html), [app/templates/guest/notices.html](../app/templates/guest/notices.html), [app/templates/guest/notice_detail.html](../app/templates/guest/notice_detail.html)
  - Admin: [app/templates/admin/dashboard.html](../app/templates/admin/dashboard.html), [app/templates/admin/notice_edit.html](../app/templates/admin/notice_edit.html)
  - Auth: [app/templates/auth/login.html](../app/templates/auth/login.html), [app/templates/auth/register.html](../app/templates/auth/register.html)
  - Moderator dashboard: [app/templates/moderator/dashboard.html](../app/templates/moderator/dashboard.html)

### Data Seeding (3rd-Year Exam)

- Added restricted 3rd-year exam notice and a reasoning-rich policy document for chatbot context:
  - File: [tests/seed_data.py](../tests/seed_data.py)
  - Notice: “Exam Schedule - 3rd Year” (CSE, year 3), with attachment.
  - ChatbotDocument: “Exam Registration (3rd Year)” policy with clear rules and examples.

### Operational Commands and Workflows

- Venv usage when activation scripts are blocked:
  - Run app:
    - `& "d:\mn\campus-management-assistant\venv\Scripts\python.exe" "d:\mn\campus-management-assistant\run.py"`
  - Install deps:
    - `& "d:\mn\campus-management-assistant\venv\Scripts\python.exe" -m pip install -r "d:\mn\campus-management-assistant\requirements.txt"`
  - Seed data:
    - `& "d:\mn\campus-management-assistant\venv\Scripts\python.exe" "d:\mn\campus-management-assistant\tests\seed_data.py"`
- Your preferred one-shot activation preface:
  - `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; . "d:\mn\campus-management-assistant\venv\Scripts\Activate.ps1";`
- Health and query tests:
  - Health: `Invoke-WebRequest -Uri http://127.0.0.1:5000/chatbot/health -Method Get | Select-Object -ExpandProperty Content | Out-String`
  - Hindi query: `$body = '{"query":"तीसरे वर्ष की परीक्षा पंजीकरण की अंतिम तिथि क्या है?"}'; Invoke-WebRequest -Uri http://127.0.0.1:5000/chatbot/query -Method Post -ContentType 'application/json' -Body $body | Select-Object -ExpandProperty Content | Out-String`

## Current Status and Observations

- Health reports `sdk: google.genai`, `model: gemini-1.5-flash`, and `ready: true` after restart.
- `/chatbot/query` still returns the model-not-supported error text for some queries under certain conditions.
  - We switched the call to `client.responses.generate(model, input)` and parse `output_text`.
  - This indicates the server is using `google.genai`, but the request shape or model availability may still mismatch expectations.

## Proposed Next Steps (Minimal, Safe)

- Adjust request format to `contents` style with roles/parts per `google.genai` recommendations to improve compatibility:
  - Construct: `contents=[{"role":"user","parts":[{"text": prompt}]}]` and call `client.responses.generate(model=..., contents=...)`.
- Add a simple runtime model check: call `client.models.get(MODEL_NAME)` at startup and log availability; if unavailable, suggest a supported model.
- Keep strict context-only prompt; ensure multilingual behavior remains.

## File Change Index

- Service: [app/services/chatbot_service.py](../app/services/chatbot_service.py)
- Routes: [app/routes/chatbot.py](../app/routes/chatbot.py), [app/routes/moderator.py](../app/routes/moderator.py)
- Templates: moderator (detail + lists), guest (home/notices/detail/chatbot), student (chatbot), admin (dashboard/notice_edit), auth (login/register)
- Static: [app/static/css/chatbot.css](../app/static/css/chatbot.css), [app/static/js/chatbot.js](../app/static/js/chatbot.js), [app/static/css/main.css](../app/static/css/main.css)
- Seed: [tests/seed_data.py](../tests/seed_data.py)
- Config: [.env](../.env)

## Notes

- No database schema changes were made.
- No student or guest permissions were altered.
- Moderator create/edit/delete flows remain unchanged; detail pages are read-only.
- We consistently avoided Python 3.12 venvs as requested; venv is Python 3.11.
