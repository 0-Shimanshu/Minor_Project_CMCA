import os
import sys
from contextlib import contextmanager

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from app.extensions import db
from app.models.user import User
from app.services.notice_service import create_notice, publish_notice


@contextmanager
def app_context():
    app = create_app()
    with app.app_context():
        yield


def main() -> int:
    # Ensure SMTP won't send real emails for this check
    os.environ['EMAIL_USER'] = ''
    os.environ['EMAIL_PASSWORD'] = ''

    with app_context():
        # Prepare a student recipient
        student = User.query.filter_by(role='student', email='student@example.com').first()
        if not student:
            student = User(
                login_id='student_test',
                password_hash='x',
                role='student',
                enrollment_no='S-TEST-001',
                department='CSE',
                year=2,
                sign_name='Student Test',
                email='student@example.com',
                is_active=True,
            )
            db.session.add(student)
            db.session.commit()

        # Create a notice and publish with notify
        from app.models.user import User as U
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(login_id='admin', password_hash='x', role='admin', is_active=True)
            db.session.add(admin)
            db.session.commit()

        ok, notice, msg = create_notice(
            admin,
            title='Email Notify Test',
            summary='This is a test notice for email notification check.',
            content='Testing email notifications when publishing a notice.',
            category_name='General',
            visibility='student',
            target_department=None,
            target_year=None,
        )
        if not ok or not notice:
            print({'ok': ok, 'message': msg})
            return 1

        ok2, msg2 = publish_notice(notice, send_email=True)
        # Query logs
        from app.models.logs import EmailLog, SystemLog
        email_logs = EmailLog.query.order_by(EmailLog.id.desc()).limit(5).all()
        system_logs = SystemLog.query.order_by(SystemLog.id.desc()).limit(10).all()
        out = {
            'create_ok': ok,
            'publish_ok': ok2,
            'email_logs_recent': [
                {
                    'id': l.id,
                    'notice_id': l.notice_id,
                    'subject': l.subject,
                    'sent_at': getattr(l, 'sent_at', None).isoformat() if getattr(l, 'sent_at', None) else None,
                } for l in email_logs
            ],
            'system_email_warnings': [
                s.message for s in system_logs if 'SMTP not configured' in (s.message or '') or 'email' in (s.module or '')
            ],
        }
        print(out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
