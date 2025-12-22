# CAMPUS MANAGEMENT ASSISTANT BOT

## Purpose

Campus management website plus AI chatbot. Provides role-based access, notices, FAQ workflow, file uploads, website scraping (admin), and an AI chatbot that answers ONLY from stored institutional data, with multilingual responses.

## Roles

- Admin: full access, manages users/notices/FAQs, scraper and logs.
- Moderator: created by admin; creates notices and answers FAQs.
- Student: registers with full enrollment number; views notices, asks FAQs, uses chatbot.
- Guest: no login; views public notices and uses public chatbot.

## Technology

- Backend: Flask
- Python: 3.10 or 3.11 ONLY (3.12 is banned)
- Database: SQLite with SQLAlchemy
- Auth: Session-based via Flask-Login (no JWT, no OAuth)
- Frontend: Jinja2 templates, plain CSS, minimal JS
- AI: Google Gemini API (no model training)

## Setup

Use Python 3.10 or 3.11 in a virtual environment. Do NOT use Python 3.12, and do NOT use versions lower than 3.10. Configure `.env` and run locally.

### Quick Start (Windows PowerShell)

```powershell
# From d:\mn\campus-management-assistant
python --version
python -m venv .\venv
. .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\run.py
```

## Environment Variables

- See the full checklist in [campus-management-assistant/docs/env-variables.md](campus-management-assistant/docs/env-variables.md).
- Required: SECRET_KEY, GEMINI_API_KEY, EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, COLLEGE_DOMAIN.

## Notes

- Emails fall back to no-reply@COLLEGE_DOMAIN and include portal links using https://COLLEGE_DOMAIN when provided.
- Admin credentials can be set via ADMIN_LOGIN_ID and ADMIN_PASSWORD or use defaults (admin / admin123).

## Forbidden Technologies (Non-Goals)

Do not use or introduce:
- FastAPI, Django, Node.js
- MongoDB/NoSQL, vector databases
- LangChain, LlamaIndex, embeddings
- Transformer training
- OAuth or social login
- Docker, microservices
- Client-side frameworks (React, Angular, Vue)

## Core Design Philosophy

- Backend enforces all permissions; frontend never enforces permissions
- Database controls visibility; AI controls understanding
- No unspecified features added; none removed
- Prefer explicit, clear, correct code over magic/optimization

## Chatbot Rules

- Answers ONLY from provided context (chatbot_documents)
- If info is missing, say so; do not hallucinate
- Student: visibility in (public, student); Guest: public only
- Prompt must instruct: respond in the same language as the user

## Multilingual Handling

- Do not manually translate or detect language
- The Gemini model handles language; prompt enforces same-language replies

## Duplicate Data Prevention

- Normalize text and store SHA-256 content_hash
- Skip insertion when content_hash exists (no duplicate knowledge)

## Global Error Handling

- Show clear user-facing messages
- Log critical errors into system_logs
- Never crash the application on failures
