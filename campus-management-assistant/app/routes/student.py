from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from . import require_role
from ..services.notice_service import student_visible_notices, student_visible_notices_by_category, list_categories, todays_student_notices
from ..services.faq_service import student_answered_faqs, submit_question, answered_faqs_filtered, todays_answered_faqs, student_asked_faqs

student_bp = Blueprint('student', __name__)


@student_bp.get('/student/dashboard')
@login_required
@require_role('student')
def dashboard():
    notices_today = todays_student_notices(current_user)
    faqs_today = todays_answered_faqs()
    my_faqs = student_asked_faqs(current_user)
    return render_template('student/dashboard.html', notices=notices_today, faqs=faqs_today, my_faqs=my_faqs)


@student_bp.get('/student/notices')
@login_required
@require_role('student')
def notices():
    category = request.args.get('category')
    items = student_visible_notices_by_category(current_user, category)
    categories = list_categories()
    return render_template('student/notices.html', notices=items, categories=categories, selected_category=category)


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


@student_bp.get('/student/faq')
@login_required
@require_role('student')
def faq():
    category = request.args.get('category')
    q = request.args.get('q')
    items = answered_faqs_filtered(category, q)
    return render_template('student/faq.html', faqs=items, selected_category=category, q=q)


@student_bp.get('/student/faq/ask')
@login_required
@require_role('student')
def ask_faq():
    return render_template('student/faq_ask.html')


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


@student_bp.get('/student/chatbot')
@login_required
@require_role('student')
def chatbot():
    # Student chatbot page
    return render_template('student/chatbot.html')
