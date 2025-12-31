from flask import Blueprint, request, redirect, url_for, jsonify, send_from_directory
from flask_login import login_required, current_user
from . import require_role
from ..services.notice_service import student_visible_notices, student_visible_notices_by_category, list_categories, todays_student_notices
from ..services.faq_service import student_answered_faqs, submit_question, answered_faqs_filtered, todays_answered_faqs, student_asked_faqs

student_bp = Blueprint('student', __name__)


@student_bp.get('/student/dashboard')
@login_required
@require_role('student')
def dashboard():
    # Serve new frontend student dashboard (no Jinja)
    return send_from_directory('frontend/student', 'dashboard.html')


@student_bp.get('/student/notices')
@login_required
@require_role('student')
def notices():
    # Serve new frontend student notices page (no Jinja)
    return send_from_directory('frontend/student', 'notices.html')


@student_bp.get('/student/notices/<int:notice_id>')
@login_required
@require_role('student')
def notice_detail(notice_id: int):
    # Reuse existing fetching logic: filter from visible list to avoid duplicating visibility rules
    visible = student_visible_notices(current_user)
    notice = next((n for n in visible if n.id == notice_id), None)
    if not notice:
        # Safe fallback: redirect to list
        return redirect(url_for('student.notices'))
    return render_template('student/notice_detail.html', notice=notice)


@student_bp.get('/api/student/notices')
@login_required
@require_role('student')
def api_student_notices():
    """Return student-visible notices with category, date, and attachments."""
    items = student_visible_notices(current_user)
    def fmt_date(dt):
        try:
            return dt.strftime('%d %b %Y') if dt else ''
        except Exception:
            return ''
    data = []
    for n in items:
        attachments = [
            {
                'id': f.id,
                'name': f.file_name or 'attachment',
                'type': f.file_type or ''
            }
            for f in getattr(n, 'files', [])
        ]
        data.append({
            'id': n.id,
            'title': n.title,
            'summary': n.summary or '',
            'content': n.content,
            'category': (n.category.name if getattr(n, 'category', None) else ''),
            'date': fmt_date(n.created_at),
            'attachments': attachments,
        })
    return jsonify({'ok': True, 'notices': data})


@student_bp.get('/student/faq')
@login_required
@require_role('student')
def faq():
    # Serve new frontend student FAQ page
    return send_from_directory('frontend/student', 'faq.html')


@student_bp.get('/student/faq/ask')
@login_required
@require_role('student')
def ask_faq():
    # Optional: serve legacy Jinja ask page (kept for backward compatibility)
    return send_from_directory('frontend/student', 'dashboard.html')


@student_bp.post('/student/faq/ask')
@login_required
@require_role('student')
def ask_faq_post():
    question = request.form.get('question', '').strip()
    category = request.form.get('category', '').strip()
    target_department = request.form.get('target_department', '').strip() or None
    ok, faq, msg = submit_question(current_user, question, category, target_department)
    if not ok:
        return render_template('student/faq_ask.html', error=msg), 400
    return redirect(url_for('student.faq'))


@student_bp.get('/api/student/faqs')
@login_required
@require_role('student')
def api_student_faqs():
    """Return answered FAQs plus the student's own asked FAQs (pending/answered)."""
    category = request.args.get('category') or None
    q = request.args.get('q') or None
    answered = answered_faqs_filtered(category=category, q=q)
    mine = student_asked_faqs(current_user)
    # Merge by id to avoid duplicates if mine includes answered ones
    by_id = {f.id: f for f in answered}
    for f in mine:
        by_id[f.id] = f

    def status_label(s: str) -> str:
        s = (s or '').strip().lower()
        return 'Answered' if s == 'answered' else 'Pending'

    def faq_json(f):
        return {
            'id': f.id,
            'question': f.question,
            'answer': f.answer or '',
            'status': status_label(f.status),
            'askedBy': getattr(current_user, 'enrollment_no', '') if f.asked_by == getattr(current_user, 'id', None) else ''
        }

    faqs = [faq_json(f) for f in by_id.values()]
    return jsonify({'ok': True, 'current_student_id': getattr(current_user, 'enrollment_no', ''), 'faqs': faqs})


@student_bp.post('/api/student/faqs')
@login_required
@require_role('student')
def api_student_submit_faq():
    data = request.get_json(silent=True) or {}
    question = str(data.get('question', '')).strip()
    category = str(data.get('category', 'General')).strip() or 'General'
    target_department = None
    if not question:
        return jsonify({'ok': False, 'message': 'Question is required'}), 400
    ok, faq, msg = submit_question(current_user, question, category, target_department)
    status = 200 if ok else 400
    return jsonify({'ok': ok, 'message': msg, 'id': getattr(faq, 'id', None)}), status


@student_bp.get('/student/chatbot')
@login_required
@require_role('student')
def chatbot():
    # Serve new frontend student chatbot page (no Jinja)
    return send_from_directory('frontend/student', 'chatbot.html')


@student_bp.get('/api/student/dashboard')
@login_required
@require_role('student')
def api_student_dashboard():
    """Aggregate dashboard data: today's notices, today's answered FAQs, and student's own FAQs."""
    notices_today = todays_student_notices(current_user)
    # Fallback to recent visible notices if none today
    from ..services.notice_service import student_visible_notices
    recent_visible = student_visible_notices(current_user)[:5]
    faqs_today = todays_answered_faqs()
    my_faqs = student_asked_faqs(current_user)
    # Limit my_faqs for dashboard view
    my_faqs_limited = my_faqs[:5]

    def fmt_date(dt):
        try:
            return dt.strftime('%d %b %Y') if dt else ''
        except Exception:
            return ''

    notices_json = [
        {
            'id': n.id,
            'title': n.title,
            'category': (n.category.name if getattr(n, 'category', None) else ''),
            'date': fmt_date(n.created_at),
        } for n in notices_today
    ]
    recent_notices_json = [
        {
            'id': n.id,
            'title': n.title,
            'category': (n.category.name if getattr(n, 'category', None) else ''),
            'date': fmt_date(n.created_at),
        } for n in recent_visible
    ]

    faqs_json = [
        {
            'id': f.id,
            'question': f.question,
            'answer': f.answer or '',
            'category': getattr(f, 'category', ''),
            'answered_at': fmt_date(getattr(f, 'answered_at', None)),
        } for f in faqs_today
    ]

    my_json = [
        {
            'id': f.id,
            'question': f.question,
            'status': f.status,
        } for f in my_faqs_limited
    ]

    user_json = {
        'name': getattr(current_user, 'sign_name', ''),
        'enrollment_no': getattr(current_user, 'enrollment_no', ''),
        'department': getattr(current_user, 'department', ''),
        'year': getattr(current_user, 'year', None),
        'status': 'Active' if getattr(current_user, 'is_active', True) else 'Inactive',
    }
    return jsonify({
        'ok': True,
        'user': user_json,
        'notices_today': notices_json,
        'recent_notices': recent_notices_json,
        'faqs_today': faqs_json,
        'my_faqs': my_json
    })


# Aliases for student frontend file names used in new pages
@student_bp.get('/student/student_dashboard.html')
@login_required
@require_role('student')
def student_dashboard_alias():
    return send_from_directory('frontend/student', 'dashboard.html')


@student_bp.get('/student/student_notices.html')
@login_required
@require_role('student')
def student_notices_alias():
    return send_from_directory('frontend/student', 'notices.html')


@student_bp.get('/student/student_chatbot.html')
@login_required
@require_role('student')
def student_chatbot_alias():
    return send_from_directory('frontend/student', 'chatbot.html')


@student_bp.get('/student/public_notices.html')
@login_required
@require_role('student')
def student_public_notices_alias():
    # Map to student notices page
    return send_from_directory('frontend/student', 'notices.html')


@student_bp.get('/student/login.html')
@login_required
@require_role('student')
def student_login_alias():
    # Serve login page from new frontend (used by logout link targets)
    return send_from_directory('frontend/auth', 'login.html')
