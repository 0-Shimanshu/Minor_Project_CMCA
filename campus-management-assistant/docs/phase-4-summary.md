# Phase 4 Summary

- Authentication implemented with Flask-Login:
  - `login_manager.login_view` and `user_loader` configured.
  - Default admin auto-created on startup from `.env` or defaults.
  - Deactivated users prevented from login; active sessions invalidated on next request.
- Auth routes (Blueprint `auth`):
  - `/auth/login` (GET/POST) with role-based redirects.
  - `/auth/register` (GET/POST) for students only with `login_id == enrollment_no` and hashed passwords.
  - `/auth/logout` redirects to `/`.
- Templates added: `auth/login.html`, `auth/register.html`.
- App factory loads auth blueprint; app imports validated in venv.
