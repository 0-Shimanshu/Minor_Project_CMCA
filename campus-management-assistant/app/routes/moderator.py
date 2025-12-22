from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import require_role
from ..services.notice_service import moderator_notices, create_notice, update_notice, attach_file, publish_notice, get_notice_for_moderator, delete_notice_owned
from ..services.faq_service import pending_faqs_for_moderator, answer_faq, get_faq, create_faq

moderator_bp = Blueprint('moderator', __name__)


@moderator_bp.get('/moderator/dashboard')
@login_required
@require_role('moderator')
def dashboard():
    notices = moderator_notices(current_user)
    pending = pending_faqs_for_moderator(current_user.department, current_user)
    return render_template('moderator/dashboard.html', notices=notices, pending_faqs=pending)


@moderator_bp.get('/moderator/notices')
@login_required
@require_role('moderator')
def notices():
    items = moderator_notices(current_user)
    return render_template('moderator/notices.html', notices=items)

@moderator_bp.get('/moderator/notices/<int:notice_id>')
@login_required
@require_role('moderator')
def notice_detail(notice_id: int):
    n = get_notice_for_moderator(notice_id, current_user)
    if not n:
        return redirect(url_for('moderator.notices'))
    return render_template('moderator/notice_detail.html', notice=n)


@moderator_bp.get('/moderator/notices/create')
@login_required
@require_role('moderator')
def notices_create():
    return render_template('moderator/notice_create.html')


@moderator_bp.post('/moderator/notices/create')
@login_required
@require_role('moderator')
def notices_create_post():
    title = request.form.get('title', '').strip()
    summary = request.form.get('summary', '').strip() or None
    content = request.form.get('content', '').strip()
    category = request.form.get('category', '').strip()
    visibility = request.form.get('visibility', '').strip()
    target_department = request.form.get('target_department', '').strip() or None
    target_year_str = request.form.get('target_year', '').strip()
    try:
        target_year = int(target_year_str) if target_year_str else None
    except ValueError:
        target_year = None

    ok, notice, msg = create_notice(current_user, title, summary, content, category, visibility, target_department, target_year)
    if not ok:
        return render_template('moderator/notice_create.html', error=msg), 400

    file = request.files.get('file')
    if file and file.filename:
        attach_ok, nf, _ = attach_file(notice, file)

    # Publish immediately; respect notify checkbox
    notify = (request.form.get('notify') in ['1', 'on', 'true', 'True'])
    publish_notice(notice, send_email=notify)

    flash('Notice created', 'success')
    return redirect(url_for('moderator.notices'))


    @moderator_bp.get('/moderator/faq/create')
    @login_required
    @require_role('moderator')
    def faq_create():
        return render_template('moderator/faq_create.html')


    @moderator_bp.post('/moderator/faq/create')
    @login_required
    @require_role('moderator')
    def faq_create_post():
        question = request.form.get('question', '').strip()
        category = request.form.get('category', '').strip()
        target_department = request.form.get('target_department', '').strip() or None
        ok, faq, msg = create_faq(question, category, target_department, current_user)
        if not ok:
            return render_template('moderator/faq_create.html', error=msg), 400
        flash('FAQ created', 'success')
        return redirect(url_for('moderator.faq_list'))


@moderator_bp.get('/moderator/notices/<int:notice_id>/edit')
@login_required
@require_role('moderator')
def notices_edit(notice_id: int):
    n = get_notice_for_moderator(notice_id, current_user)
    if not n:
        return redirect(url_for('moderator.notices'))
    return render_template('moderator/notice_edit.html', notice=n)


@moderator_bp.post('/moderator/notices/<int:notice_id>/edit')
@login_required
@require_role('moderator')
def notices_edit_post(notice_id: int):
    n = get_notice_for_moderator(notice_id, current_user)
    if not n:
        return redirect(url_for('moderator.notices'))
    fields = {
        'title': request.form.get('title', '').strip(),
        'summary': request.form.get('summary', '').strip() or None,
        'content': request.form.get('content', '').strip(),
    }
    update_notice(n, **fields)
    flash('Notice updated', 'success')
    return redirect(url_for('moderator.notices'))


@moderator_bp.post('/moderator/notices/<int:notice_id>/delete')
@login_required
@require_role('moderator')
def notices_delete_post(notice_id: int):
    ok, _ = delete_notice_owned(notice_id, current_user)
    if ok:
        flash('Notice deleted', 'success')
    else:
        flash('Delete failed', 'error')
    return redirect(url_for('moderator.notices'))


@moderator_bp.get('/moderator/faq')
@login_required
@require_role('moderator')
def faq_list():
    items = pending_faqs_for_moderator(current_user.department, current_user)
    return render_template('moderator/faq.html', faqs=items)

@moderator_bp.get('/moderator/faq/<int:faq_id>')
@login_required
@require_role('moderator')
def faq_detail_view(faq_id: int):
    f = get_faq(faq_id)
    if not f:
        return redirect(url_for('moderator.faq_list'))
    return render_template('moderator/faq_detail.html', faq=f)


@moderator_bp.get('/moderator/faq/<int:faq_id>/answer')
@login_required
@require_role('moderator')
def faq_answer(faq_id: int):
    f = get_faq(faq_id)
    if not f:
        return redirect(url_for('moderator.faq_list'))
    return render_template('moderator/faq_answer.html', faq=f)


@moderator_bp.post('/moderator/faq/<int:faq_id>/answer')
@login_required
@require_role('moderator')
def faq_answer_post(faq_id: int):
    f = get_faq(faq_id)
    if not f:
        return redirect(url_for('moderator.faq_list'))
    answer = request.form.get('answer', '').strip()
    ok, msg = answer_faq(f, answer, current_user)
    if ok:
        flash('FAQ answered', 'success')
    else:
        flash('Answer failed', 'error')
    return redirect(url_for('moderator.faq_list'))
