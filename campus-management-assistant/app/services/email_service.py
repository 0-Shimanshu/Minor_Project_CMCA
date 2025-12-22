import os
import smtplib
from email.message import EmailMessage
from typing import List, Tuple
from ..extensions import db
from ..models.user import User
from ..models.notice import Notice
from ..models.logs import EmailLog, SystemLog

HOST = os.getenv('EMAIL_HOST')
PORT = int(os.getenv('EMAIL_PORT', '587'))
USER = os.getenv('EMAIL_USER')
PASSWORD = os.getenv('EMAIL_PASSWORD')
DOMAIN = os.getenv('COLLEGE_DOMAIN')
USE_SSL = (os.getenv('EMAIL_USE_SSL', '').lower() in ('1', 'true', 'yes')) or PORT == 465
USE_TLS = (os.getenv('EMAIL_USE_TLS', 'true').lower() in ('1', 'true', 'yes')) and not USE_SSL


def _eligible_students_for_notice(notice: Notice) -> List[User]:
    q = User.query.filter_by(role='student', is_active=True)
    if notice.visibility == 'restricted':
        if notice.target_department:
            q = q.filter_by(department=notice.target_department)
        if notice.target_year is not None:
            q = q.filter_by(year=notice.target_year)
    # public/student → all active students
    return q.all()


def _create_email(notice: Notice, recipient: str) -> EmailMessage:
    msg = EmailMessage()
    msg['Subject'] = f"New Notice: {notice.title}"
    from_addr = USER or (f"no-reply@{DOMAIN}" if DOMAIN else 'no-reply@example.com')
    msg['From'] = from_addr
    msg['To'] = recipient
    summary = notice.summary or ''
    base_url = f"https://{DOMAIN}" if DOMAIN else ''
    notices_url = f"{base_url}/student/notices" if base_url else "/student/notices"
    body = (
        f"A new notice has been published.\n\nTitle: {notice.title}\nSummary: {summary}\nVisibility: {notice.visibility}\n\n"
        f"Visit the portal to read more: {notices_url}\n"
    )
    msg.set_content(body)
    return msg


def send_notice_published(notice: Notice) -> Tuple[int, int]:
    attempted = 0
    success = 0
    try:
        recipients = [u.email for u in _eligible_students_for_notice(notice) if u.email]
        if not recipients or not HOST or not USER or not PASSWORD:
            db.session.add(SystemLog(module='email', message='email not configured or no recipients'))
            db.session.commit()
            return attempted, success
        if USE_SSL:
            smtp_client = smtplib.SMTP_SSL(HOST, PORT, timeout=20)
        else:
            smtp_client = smtplib.SMTP(HOST, PORT, timeout=20)
        with smtp_client as smtp:
            if USE_TLS:
                try:
                    smtp.starttls()
                except Exception as e:
                    db.session.add(SystemLog(module='email', message=f'starttls failed: {e}'))
                    db.session.commit()
                    return attempted, success
            smtp.login(USER, PASSWORD)
            for r in recipients:
                attempted += 1
                try:
                    msg = _create_email(notice, r)
                    smtp.send_message(msg)
                    success += 1
                except Exception as e:
                    db.session.add(SystemLog(module='email', message=f'send failed for {r}: {e}'))
                    db.session.commit()
        # Log one entry per notice publication
        db.session.add(EmailLog(notice_id=notice.id, sent_by=notice.created_by, subject=f"New Notice: {notice.title}"))
        db.session.commit()
    except Exception as e:
        try:
            db.session.add(SystemLog(module='email', message=f'bulk send error: {e}'))
            db.session.commit()
        except Exception:
            pass
    return attempted, success
