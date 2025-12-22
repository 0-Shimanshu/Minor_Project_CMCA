# Phase 6 Summary

- Implemented notices and FAQs core features:
  - Services: notice lifecycle (create/update/publish with attachments and chatbot document creation), FAQ lifecycle (pending → answered and chatbot document creation).
  - Visibility: guest sees public/published; student sees public/student/restricted based on department/year; moderator sees own; admin sees all.
  - Routes: guest, student, moderator, admin blueprints wired to services with role guards.
  - Templates: pages for lists, create/edit, and FAQ ask/answer.
- Validated: App imports and all templates compile under venv.
