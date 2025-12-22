# 117-Point Compliance Check (Grouped by 10)

This document summarizes what was checked, observed, and changed for each 10-point group so far.

## Group 1–10
- Checks:
  - Project purpose and scope match the spec (campus portal + chatbot).
  - Technology stack uses Flask and Python 3.10/3.11 only.
  - Forbidden technologies are not present.
  - Chatbot core rules: context-only answers; no external knowledge.
  - Multilingual handling: reply in same language; no manual detection.
  - Duplicate prevention: plan to store SHA-256 content_hash.
  - Development order respected; global error handling defined.
- Observations:
  - README wording implied “next 3.11 only”; needs “3.10 or 3.11 ONLY.”
  - Forbidden tech list and core philosophy were not fully captured.
  - Chatbot/multilingual/dedup rules not explicitly documented.
- Changes:
  - Updated README to: 
    - Enforce Python 3.10/3.11 ONLY; 3.12 banned.
    - Add forbidden tech list and core design philosophy.
    - Document chatbot rules, multilingual handling, and dedup requirement.
    - Clarify global error handling expectations.

## Group 11–20
- Checks:
  - Python version policy, venv usage, exact requirements.txt contents.
  - .env variables required by config.
  - app/config.py loads env; uses absolute DB path at app/database/app.db.
  - run.py starts app via factory; no business logic/routes inside.
  - .gitignore includes venv, .env, __pycache__, *.pyc, uploads, *.db.
  - First startup checkpoint: app imports; DB is created.
- Observations:
  - requirements.txt matches the exact required list.
  - config.py uses absolute DB path; run.py uses factory pattern correctly.
  - .gitignore missing explicit app/uploads/ ignore.
  - Startup import succeeds; DB file created.
- Changes:
  - Updated .gitignore to include app/uploads/.
  - Clarified README wording on Python version policy.
  - Validated app factory import and DB existence.

## Group 21–30
- Checks:
  - Root structure: campus-management-assistant with .env, .gitignore, README.md, requirements.txt, run.py, venv/.
  - app/ structure: __init__.py, config.py, extensions.py, models/, routes/, services/, templates/, static/, uploads/, database/.
  - app/__init__.py follows factory pattern; extensions initialized; blueprints registered.
  - extensions.py defines db and login_manager.
  - templates: base.html and role subfolders exist; pages extend base.
  - static: css/js/images present.
  - uploads: notices/ and scraped/ present.
  - database: app/database/app.db present.
- Observations:
  - All required folders/files exist and are populated.
  - Routes call service-layer functions instead of direct DB queries (verified on guest/student/moderator).
  - Template sets are present for all roles.
  - No structural gaps against points 21–30.
- Changes:
  - No structural changes required; only earlier README/.gitignore adjustments applied.

## Workspace Hygiene
- Removed duplicate files previously created outside the project root to prevent conflicts.
- Kept d:\mn/campus-management-assistant as the single source of truth.

## Next Steps
- Continue with groups 31–40 using the same flow: plan → check → implement minimal changes, and update this document after each batch.

## Group 31–40
- Checks:
  - Database directory exists at app/database and the SQLite file app.db is created on startup.
  - Architectural guarantees: models isolated from routes; routes call services; services enforce business logic; templates are passive.
  - Database design matches the spec strictly:
    - users: id, login_id, password_hash, role, enrollment_no, department, year, sign_name, email, is_active, created_at.
    - notice_categories: id, name (unique, required).
    - notices: id, title, summary, content, category_id (FK), visibility, status, target_department, target_year, created_by (FK), created_at.
    - notice_files: id, notice_id (FK), file_name, file_path, file_type, uploaded_at.
    - faqs: id, question, answer, category, target_department, status, asked_by (FK), answered_by (FK), created_at, answered_at.
    - chatbot_documents: id, source_type, source_id, content, content_hash (unique), visibility, created_at.
    - scraped_websites: id, url (unique), added_at.
    - scrape_logs (previewed for upcoming groups): id, website_id (FK), status, extracted_text_length, pdf_links_found, scraped_at.
  - Relationships: `Notice.files` delete-orphan, FAQ asker/answerer relationships, and scraper log relationship present.
- Observations:
  - Column sets match exactly; uniqueness and non-null constraints align with the spec.
  - Allowed value sets (e.g., visibility/status) are enforced in services rather than via DB constraints, which is acceptable per spec.
  - Absolute DB path and directory creation are implemented in config/app factory.
- Changes:
  - No model or DB changes were required; confirmed compliance.


## Group 41–50
- Checks:
  - Scrape logs, email logs, and system logs tables exist with required columns.
  - Database initialization uses `db.create_all()` and ensures the DB directory exists.
  - Data safety guarantees: draft data not exposed to chatbot; deactivated users blocked; no unintended cascade deletes except explicit notice-file orphan removal.
  - Authentication is session-based via Flask-Login; no JWT/OAuth/tokens.
  - Passwords stored hashed (`generate_password_hash` / `check_password_hash`).
  - Login uses `login_id` only; student registration maps `login_id = enrollment_no` and sets role `student`.
  - Student registration collects department/year/password (plus email) and prevents duplicates; students cannot edit profiles.
  - Login flow: user fetched by `login_id`, active status checked, password verified; friendly errors logged to `system_logs`.
- Observations:
  - `auth_service.authenticate()` logs all failure modes and returns clear messages.
  - `auth_service.register_student()` enforces uniqueness and hashes passwords.
  - Deactivation behavior supported via service helper and session logic.
  - User deletion is attempted via service; foreign key constraints protect historical data.
- Changes:
  - No code changes required for 41–50; confirmed compliance.


## Group 51–60
- Checks:
  - Role-based redirects after login route to correct dashboards.
  - Logout redirects to guest home.
  - Deactivated users cannot log in; sessions invalidated via before_request.
  - Route protection: requires authentication and correct role; violations logged and show user-friendly messages.
  - Base layout provides role-aware navigation for each role; guest UI offers public notices and chatbot.
- Observations:
  - Base nav already distinguishes roles and includes required links.
  - Guest home linked to `/guest/chatbot`, while spec requires `/chatbot`.
  - Student chatbot link existed in nav; route was missing.
  - Route protection logged violations but did not flash messages.
- Changes:
  - Added guest chatbot routes `/chatbot` (spec) and `/guest/chatbot` (template alias) rendering `guest/chatbot.html`.
  - Added student chatbot route `/student/chatbot` rendering `student/chatbot.html` with role protection.
  - Enhanced `require_role()` to flash clear messages on auth/authorization failures while still logging to `system_logs`.


## Group 61–70
- Checks:
  - Guest notices list shows only `visibility='public'` and `status='published'`; detail view includes attachments.
  - Guest chatbot page exists and uses public chatbot documents.
  - Student dashboard displays today’s notices (visibility rules), today’s answered FAQs, and student’s asked FAQs with statuses.
  - Student notices page supports category filter; FAQ page supports category filter + search; Ask FAQ form includes question, category, target department.
  - Student Ask FAQ submission sets `status='pending'`, links `asked_by`, and students have no edit route.
  - Student chatbot uses visibility in (`public`,`student`) without department/year filtering.
  - Moderator dashboard shows only their notices and pending FAQs for their department.
  - Moderator notices: can view, create, edit, delete their own notices.
  - On publish, chatbot_document is created with deduplication; PDFs extracted when possible; email notification attempted and logged on failure.
- Observations:
  - All student and guest routes/templates exist and call services; visibility is enforced in service queries.
  - Moderator delete route was missing; restricted visibility validation on create was not enforced.
- Changes:
  - Added restricted create validation in `notice_service.create_notice()` to require department and year when visibility is `restricted`.
  - Added moderator delete route `/moderator/notices/<id>/delete` and service `delete_notice_owned()` with safe file removal and ownership checks.
  - Confirmed publish creates chatbot documents and emails are sent via service with non-blocking failure handling.


## Group 71–80
- Checks:
  - Moderator FAQ page shows pending FAQs filtered by target department; moderator can answer and create FAQs.
  - Moderator answer page marks FAQ as answered and creates a chatbot document entry.
  - Admin dashboard shows recently published notices, recently answered FAQs, and recent email notifications.
  - Admin users page lists students and moderators; allows search and deactivation.
  - Admin notices page supports view, create, edit, delete, and publish flow.
  - Admin FAQ page supports create and answer pending FAQs.
  - Admin scraper page supports adding URLs, triggering scraping, and viewing logs (PDF handling will be validated in later groups).
  - Admin logs page displays system and email logs.
  - UI error handling: friendly messages and logging; destructive actions require confirmation; no empty pages.
- Observations:
  - Admin routes previously only rendered templates; actions for CRUD and recents were missing.
  - Logs listing was implemented via service helpers; dashboard lacked email section.
- Changes:
  - Added admin dashboard recents (published notices, answered FAQs) and recent email notifications.
  - Implemented admin users search and activation/deactivation/deletion endpoints.
  - Implemented admin notices create/edit/publish/delete endpoints using service-layer checks.
  - Implemented admin FAQ create and answer endpoints; reuse moderator answer template.
  - Confirmed scraper admin page is provided by the scraper blueprint; logs view remains.
  - Ensured delete actions are POST-only and templates include confirmation prompts.


## Group 81–90
- Checks:
  - Service layer boundaries: all business logic lives in services; routes remain thin; templates stay passive.
  - Notice service: create/update/delete/attach/publish; visibility enforced; publish creates chatbot_documents with dedup.
  - Notice file handling: uploads to app/uploads/notices; file path stored only; allowed types (pdf/image); safe deletion on notice delete.
  - PDF handling: `pdf_service.extract_pdf_text()` uses pdfplumber; failure logs to system_logs; empty text skipped.
  - FAQ service: submit/answer; answered visible; chatbot doc created on answer with dedup; student cannot edit.
  - Chatbot service: role-based doc fetch; prompt enforces context-only answers and same-language replies; graceful error handling.
  - Deduplication: content normalized and SHA-256 content_hash checked before insertion for notices, FAQs, scrape text/PDF.
  - Scraper service: fetch HTML, extract visible text, detect PDFs, save logs; scraped content default visibility = public; dedup applied.
  - Email service: send notifications on publish; log email attempts; failures do not block publishing.
  - System logging: errors and key events recorded into system_logs across services.
- Observations:
  - All services meet the spec; dedup implemented consistently; visibility and error handling enforced.
  - Email sender uses `no-reply@COLLEGE_DOMAIN` fallback when env not configured.
- Changes:
  - No code changes required; confirmed compliance for 81–90.


## Group 91–100
- Checks:
  - Chatbot routing provides a POST-only JSON endpoint at `/chatbot/query` per spec.
  - Role determination for JSON queries: unauthenticated = guest; student = student; others treated as guest.
  - Chatbot prompt uses the exact instruction: answer only from provided context; if not found say "I don't have enough information"; respond in the same language; no external knowledge.
  - Context sent to the model excludes any metadata (ids, sources) to avoid leakage.
  - Error handling returns concise JSON with `ok` and `answer`; HTTP status reflects success or client error.
- Observations:
  - Existing chatbot pages used form POSTs but lacked a JSON query endpoint.
  - Prompt wording included assistant persona and embedded metadata tags in context blocks.
- Changes:
  - Added `/chatbot/query` POST endpoint returning JSON, using `current_user` to select role (student vs guest).
  - Updated `chatbot_service.ask_gemini()` to use strict instruction text and removed metadata from the context builder.
  - Ensured errors and empty queries return clear messages and appropriate HTTP status codes.


## Group 101–110
- Checks:
  - Multilingual behavior: replies in the same language as the user's question without manual language detection.
  - Chatbot failure handling: empty query, missing API key, empty context, and model errors return friendly messages.
  - Generation rules: answers only from provided context; no external knowledge; strict instruction format maintained.
  - Dedup consistency reaffirmed across notices, FAQs, and scraped content.
  - Guest UI uses the canonical `/chatbot` route.
- Observations:
  - Guest home page linked to `/guest/chatbot` (alias) instead of the canonical `/chatbot`.
- Changes:
  - Updated guest home link to `/chatbot` for consistency with the spec.
  - Reverified chatbot error messages and kept them concise and user-friendly.


## Group 111–117
- Checks:
  - Admin logs pages list recent system and email logs with sensible limits; routes render without errors.
  - No forbidden technologies introduced; Python 3.10/3.11 policy upheld; 3.12 remains banned.
  - Destructive actions (delete, publish) and chatbot JSON use POST-only.
  - Documentation completeness: README and 117-point checklist reflect final architecture, endpoints, and rules.
- Observations:
  - `logs_service` enforces default limits (50) for listing logs; admin templates display them.
  - README already documents chatbot rules, multilingual constraints, and dedup.
- Changes:
  - No code changes required; confirmed compliance and finalized documentation.

