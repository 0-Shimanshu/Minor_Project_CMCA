# Environment Variables

This app reads configuration from `.env` at the project root. Below is a concise checklist of what you (the deploying admin) need to provide vs. what has sensible defaults.

## Must Provide (from your institution/provider)
- SECRET_KEY: Strong random string for session security.
- GEMINI_API_KEY: Google Generative AI key for chatbot.
- EMAIL_HOST: SMTP server host (from your IT/provider).
- EMAIL_PORT: SMTP port (common: 587 STARTTLS, 465 SSL).
- EMAIL_USER: SMTP username (often the email address).
- EMAIL_PASSWORD: SMTP password or app password.
- COLLEGE_DOMAIN: Primary domain for your institution (e.g., `acropolis.in`).
- ADMIN_LOGIN_ID: Optional, default `admin` if omitted.
- ADMIN_PASSWORD: Optional, default `admin123` if omitted.

## Defaults We Provide (you can override)
- EMAIL_PORT: Defaults to `587` if not set.
- From Address: If `EMAIL_USER` is absent, emails fall back to `no-reply@COLLEGE_DOMAIN` (or `no-reply@example.com` if `COLLEGE_DOMAIN` is not set).
- Portal Links: Emails include `https://COLLEGE_DOMAIN/...` if `COLLEGE_DOMAIN` is set; otherwise relative paths.

## Example `.env`
```
SECRET_KEY=change_this_secret
GEMINI_API_KEY=your_gemini_api_key
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USER=example@acropolis.in
EMAIL_PASSWORD=your_email_password
COLLEGE_DOMAIN=acropolis.in
ADMIN_LOGIN_ID=admin
ADMIN_PASSWORD=admin123
```

## How to obtain SMTP host/port
- Check your email provider’s SMTP settings docs (e.g., Microsoft 365, Google Workspace, Zoho).
- Typical values: Host like `smtp.office365.com` or `smtp.gmail.com`; Port `587` (STARTTLS) or `465` (SSL).
- Your IT team should confirm the exact host, port, and whether STARTTLS/SSL is required.
