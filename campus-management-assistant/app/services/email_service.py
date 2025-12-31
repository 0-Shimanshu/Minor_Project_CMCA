import os
import smtplib
from email.message import EmailMessage
from typing import List, Tuple
from datetime import datetime
from flask import render_template
import smtplib
from ..extensions import db
from ..models.user import User
from ..models.notice import Notice
from ..models.logs import EmailLog, SystemLog

DOMAIN = os.getenv('COLLEGE_DOMAIN')
SMTP_SERVER = os.getenv('EMAIL_HOST', 'localhost')
SMTP_PORT = int(os.getenv('EMAIL_PORT', '587'))
SMTP_USERNAME = os.getenv('EMAIL_USER', '')
SMTP_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'
USE_SSL = os.getenv('EMAIL_USE_SSL', 'false').lower() == 'true'
FROM_EMAIL = os.getenv('FROM_EMAIL', f"no-reply@{DOMAIN}" if DOMAIN else 'no-reply@example.com')


def _eligible_students_for_notice(notice: Notice) -> List[User]:
    q = User.query.filter_by(role='student', is_active=True)
    if notice.visibility == 'restricted':
        if notice.target_department:
            q = q.filter_by(department=notice.target_department)
        if notice.target_year is not None:
            q = q.filter_by(year=notice.target_year)
    # public/student → all active students
    return q.all()


def _create_email(notice: Notice, recipient: str, recipient_name: str = "Student") -> EmailMessage:
    """Create a professional HTML email message for notice publication."""
    msg = EmailMessage()
    msg['Subject'] = f"📢 New Notice: {notice.title}"
    msg['From'] = FROM_EMAIL
    msg['To'] = recipient
    
    # Determine importance level based on visibility or other factors
    importance = 'high' if notice.visibility == 'urgent' else 'normal'
    
    # Format visibility label
    visibility_label = notice.visibility.title() if notice.visibility else 'Public'
    
    # Get category name
    category = getattr(notice.category, 'name', 'General') if notice.category else 'General'
    
    # Get published by (user who created the notice)
    published_by = getattr(getattr(notice, 'author', None), 'sign_name', None) or getattr(getattr(notice, 'author', None), 'login_id', None) or 'Administrator'
    
    # Format dates
    published_date = notice.created_at.strftime('%B %d, %Y at %I:%M %p') if notice.created_at else 'Recently'
    
    # Portal URLs
    base_url = f"https://{DOMAIN}" if DOMAIN else "http://localhost:5000"
    portal_url = f"{base_url}/student/notices"
    support_email = f"mailto:support@{DOMAIN}" if DOMAIN else "mailto:support@example.com"
    
    # Prepare template context
    context = {
        'recipient_name': recipient_name,
        'notice_title': notice.title,
        'category': category,
        'visibility_label': visibility_label,
        'published_date': published_date,
        'published_by': published_by,
        'summary': notice.summary or '',
        'target_dept': notice.target_department or None,
        'target_year': str(notice.target_year) if notice.target_year is not None else None,
        'importance': importance,
        'portal_url': portal_url,
        'support_email': support_email,
        'current_year': datetime.utcnow().year,
    }
    
    # Render HTML from template
    try:
        html_content = render_template('email/notice_published.html', **context)
    except Exception as e:
        # Fallback to plain text if template rendering fails
        html_content = _create_fallback_email_html(notice, context)
    
    msg.set_content("Please use an email client that supports HTML to view this message.")
    msg.add_alternative(html_content, subtype='html')
    
    return msg


def _create_fallback_email_html(notice: Notice, context: dict) -> str:
    """Create fallback HTML email if template rendering fails."""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2>New Notice: {context['notice_title']}</h2>
                <p>Hello {context['recipient_name']},</p>
                <p>A new notice has been published:</p>
                <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Title:</strong> {context['notice_title']}</p>
                    <p><strong>Category:</strong> {context['category']}</p>
                    <p><strong>Visibility:</strong> {context['visibility_label']}</p>
                    <p><strong>Published:</strong> {context['published_date']}</p>
                    <p><strong>By:</strong> {context['published_by']}</p>
                    {f'<p><strong>Summary:</strong> {context["summary"]}</p>' if context['summary'] else ''}
                </div>
                <p><a href="{context['portal_url']}" style="color: #667eea; text-decoration: none;">View on Portal</a></p>
            </div>
        </body>
    </html>
    """


def send_notice_published(notice: Notice) -> Tuple[int, int]:
    """Send email notifications to eligible students about a newly published notice.
    
    Returns (attempted, success) counts.
    """
    recipients = [u.email for u in _eligible_students_for_notice(notice) if u.email]
    
    if not recipients:
        # No eligible recipients, but still log the publication
        category = getattr(notice.category, 'name', 'General')
        visibility = notice.visibility
        dept = notice.target_department or 'All Departments'
        year = str(notice.target_year) if notice.target_year is not None else 'All Years'
        subject = f"Notice Published • {notice.title} • Category: {category} • Visibility: {visibility} • Dept: {dept} • Year: {year}"
        
        log = EmailLog()
        log.notice_id = notice.id
        log.sent_by = notice.created_by
        log.subject = subject
        log.status = 'sent'
        db.session.add(log)
        db.session.commit()
        return 0, 0
    
    attempted = len(recipients)
    success = 0
    
    # Build subject for logging
    category = getattr(notice.category, 'name', 'General')
    visibility = notice.visibility
    dept = notice.target_department or 'All Departments'
    year = str(notice.target_year) if notice.target_year is not None else 'All Years'
    subject = f"Notice Published • {notice.title} • Category: {category} • Visibility: {visibility} • Dept: {dept} • Year: {year}"
    
    # Only send if SMTP is configured
    if SMTP_USERNAME and SMTP_PASSWORD:
        try:
            for recipient in recipients:
                try:
                    user = User.query.filter_by(email=recipient).first()
                    recipient_name = (getattr(user, 'sign_name', None) or getattr(user, 'login_id', None) or "Student") if user else "Student"

                    msg = _create_email(notice, recipient, recipient_name)

                    # Send via SMTP (SSL or TLS) with robust EHLO/STARTTLS
                    if USE_SSL:
                        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                            server.ehlo()
                            server.login(SMTP_USERNAME, SMTP_PASSWORD)
                            server.send_message(msg)
                    else:
                        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                            server.ehlo()
                            if USE_TLS:
                                server.starttls()
                                server.ehlo()
                            server.login(SMTP_USERNAME, SMTP_PASSWORD)
                            server.send_message(msg)

                    success += 1
                except smtplib.SMTPAuthenticationError as e:
                    db.session.add(SystemLog(
                        module='email',
                        message=(
                            f"SMTP auth failed for notice_id={notice.id}: code={getattr(e, 'smtp_code', None)} msg={getattr(e, 'smtp_error', e)}. "
                            "Check EMAIL_USER/EMAIL_PASSWORD (use provider App Password), TLS/SSL settings, and FROM_EMAIL."
                        )
                    ))
                    db.session.commit()
                    continue
                except Exception as e:
                    db.session.add(SystemLog(
                        module='email',
                        message=f"Failed to send notice email to {recipient}: {e} notice_id={notice.id}"
                    ))
                    db.session.commit()
                    continue
        except Exception as e:
            db.session.add(SystemLog(
                module='email',
                message=f"SMTP connection error for notice_id={notice.id}: {e}"
            ))
            db.session.commit()
    else:
        # No SMTP configured - log a warning but don't fail
        db.session.add(SystemLog(
            module='email',
            message=f"SMTP not configured. Emails would have been sent to {attempted} recipients for notice_id={notice.id}"
        ))
        db.session.commit()
    
    # Log the notice publication
    log = EmailLog()
    log.notice_id = notice.id
    log.sent_by = notice.created_by
    log.subject = subject
    log.status = 'sent' if success > 0 or not (SMTP_USERNAME and SMTP_PASSWORD) else 'failed'
    db.session.add(log)
    db.session.commit()
    
    return attempted, success
