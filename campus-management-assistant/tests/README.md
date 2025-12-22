# Test Suite

This folder contains a lightweight, app-integrated test suite to seed data and verify core features without refactoring the project.

## Contents
- `seed_data.py`: Seeds users, categories, notices (public/student/restricted), attachments (dummy PDFs), and FAQs.
- `test_routes.py`: Verifies guest/student routes, secure downloads, login, student notice detail page, and chatbot JSON behavior.
- `test_moderator_admin.py`: Moderator CRUD flows and admin logs/notices views.
- `test_admin_users_scraper_auth.py`: Admin users activate/deactivate/delete, scraper add/list, FAQ create/answer, and auth failure logging.
- `run_tests.py`: Convenience runner that seeds then runs route tests.

## Prerequisites
- Activate venv and ensure the app imports:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& d:\mn\campus-management-assistant\venv\Scripts\Activate.ps1
```

## Run
- Seed data + run tests:
```powershell
& d:\mn\campus-management-assistant\venv\Scripts\python.exe d:\mn\campus-management-assistant\tests\run_tests.py
```

- Run seeding alone:
```powershell
& d:\mn\campus-management-assistant\venv\Scripts\python.exe d:\mn\campus-management-assistant\tests\seed_data.py
```

- Run route tests only:
```powershell
& d:\mn\campus-management-assistant\venv\Scripts\python.exe d:\mn\campus-management-assistant\tests\test_routes.py
```

- Run admin/users/scraper/auth tests only:
```powershell
& d:\mn\campus-management-assistant\venv\Scripts\python.exe d:\mn\campus-management-assistant\tests\test_admin_users_scraper_auth.py
```

## Notes
- No schema or service refactors are performed.
- Scraped PDFs remain non-downloadable; emails senders are not configured; the suite expects graceful failures logged.
- Chatbot JSON endpoint is tested without an API key; response should indicate configuration is missing.
