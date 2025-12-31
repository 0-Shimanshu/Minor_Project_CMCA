from flask import Blueprint, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user
from . import require_role
from ..services.notice_service import moderator_notices, create_notice, update_notice, attach_file, publish_notice, get_notice_for_moderator, delete_notice_owned
from ..services.faq_service import pending_faqs_for_moderator, answer_faq, get_faq, create_faq

moderator_bp = Blueprint('moderator', __name__)


@moderator_bp.get('/moderator/dashboard')
@login_required
@require_role('moderator')
def dashboard():
    # Serve new frontend moderator dashboard (no Jinja)
    return send_from_directory('frontend/moderator', 'dashboard.html')


@moderator_bp.get('/moderator/notices')
@login_required
@require_role('moderator')
def notices():
    # Serve new frontend moderator notices page (no Jinja)
    return send_from_directory('frontend/moderator', 'notices.html')

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
    return send_from_directory('frontend/moderator', 'notices.html')


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
        return send_from_directory('frontend/moderator', 'notices.html')


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
    # Serve new frontend moderator FAQ queue page
    return send_from_directory('frontend/moderator', 'faq.html')

@moderator_bp.get('/api/moderator/dashboard')
@login_required
@require_role('moderator')
def api_moderator_dashboard():
    """Return moderator dashboard stats and recent items."""
    my_notices = moderator_notices(current_user)
    pending = pending_faqs_for_moderator(getattr(current_user, 'department', None), current_user)

    # Count of answered by current moderator
    from ..services.faq_service import answered_faqs
    answered_all = answered_faqs()
    answered_by_me = [f for f in answered_all if getattr(f, 'answered_by', None) == getattr(current_user, 'id', None)]

    def fmt_date(dt):
        try:
            return dt.strftime('%d %b %Y') if dt else ''
        except Exception:
            return ''

    # Only show student-asked or my-created FAQs in pending list
    def visible_to_me(faq):
        asker = getattr(faq, 'asker', None)
        role = getattr(asker, 'role', None)
        return (role == 'student' or asker is None or getattr(asker, 'id', None) == getattr(current_user, 'id', None))

    recent_pending = [
        {
            'id': f.id,
            'question': f.question,
            'category': getattr(f, 'category', ''),
            'askedBy': (getattr(getattr(f, 'asker', None), 'sign_name', '') or ''),
            'created_at': fmt_date(getattr(f, 'created_at', None)),
        } for f in pending if visible_to_me(f)
    ][:20]

    recent_my_notices = [
        {
            'id': n.id,
            'title': n.title,
            'category': getattr(getattr(n, 'category', None), 'name', ''),
            'status': getattr(n, 'status', ''),
            'visibility': getattr(n, 'visibility', ''),
            'created_at': fmt_date(getattr(n, 'created_at', None)),
        } for n in my_notices[:20]
    ]

    # My created FAQs (pending or answered)
    try:
        from ..models.faq import FAQ
        my_faqs = FAQ.query.filter(FAQ.asked_by == getattr(current_user, 'id', None)).order_by(FAQ.created_at.desc()).limit(20).all()
        recent_my_faqs = [
            {
                'id': f.id,
                'question': f.question,
                'status': getattr(f, 'status', ''),
                'created_at': fmt_date(getattr(f, 'created_at', None)),
            } for f in my_faqs
        ]
    except Exception:
        recent_my_faqs = []

    user_json = {
        'name': getattr(current_user, 'sign_name', '') or getattr(current_user, 'name', ''),
        'id': getattr(current_user, 'id', None),
        'role': getattr(current_user, 'role', ''),
        'department': getattr(current_user, 'department', ''),
    }
    return jsonify({
        'ok': True,
        'user': user_json,
        'stats': {
            'pending_faqs': len(pending),
            'answered_by_me': len(answered_by_me),
            'my_notices': len(my_notices),
        },
        'recent_pending_faqs': recent_pending,
        'recent_my_notices': recent_my_notices,
        'recent_my_faqs': recent_my_faqs,
    })

@moderator_bp.get('/api/moderator/notices')
@login_required
@require_role('moderator')
def api_moderator_notices():
    items = moderator_notices(current_user)
    def fmt_date(dt):
        try:
            return dt.strftime('%d %b %Y') if dt else ''
        except Exception:
            return ''
    data = [
        {
            'id': n.id,
            'title': n.title,
            'category': getattr(getattr(n, 'category', None), 'name', ''),
            'status': getattr(n, 'status', ''),
            'visibility': getattr(n, 'visibility', ''),
            'target_department': getattr(n, 'target_department', None),
            'target_year': getattr(n, 'target_year', None),
            'created_at': fmt_date(getattr(n, 'created_at', None)),
        } for n in items
    ]
    return jsonify({'ok': True, 'notices': data})

@moderator_bp.get('/api/moderator/notices/<int:notice_id>')
@login_required
@require_role('moderator')
def api_moderator_notice_detail(notice_id: int):
    n = get_notice_for_moderator(notice_id, current_user)
    if not n:
        return jsonify({'ok': False, 'message': 'Not found'}), 404
    def fmt_date(dt):
        try:
            return dt.strftime('%d %b %Y') if dt else ''
        except Exception:
            return ''
    data = {
        'id': n.id,
        'title': n.title,
        'summary': getattr(n, 'summary', '') or '',
        'content': getattr(n, 'content', '') or '',
        'category': getattr(getattr(n, 'category', None), 'name', ''),
        'status': getattr(n, 'status', ''),
        'visibility': getattr(n, 'visibility', ''),
        'target_department': getattr(n, 'target_department', None),
        'target_year': getattr(n, 'target_year', None),
        'created_at': fmt_date(getattr(n, 'created_at', None)),
    }
    return jsonify({'ok': True, 'notice': data})

@moderator_bp.post('/api/moderator/notices/<int:notice_id>/publish')
@login_required
@require_role('moderator')
def api_moderator_publish_notice(notice_id: int):
    n = get_notice_for_moderator(notice_id, current_user)
    if not n:
        return jsonify({'ok': False, 'message': 'Not found'}), 404
    ok, msg = publish_notice(n, send_email=False)
    status = 200 if ok else 400
    return jsonify({'ok': ok, 'message': msg}), status

@moderator_bp.post('/api/moderator/notices/<int:notice_id>/delete')
@login_required
@require_role('moderator')
def api_moderator_delete_notice(notice_id: int):
    ok, msg = delete_notice_owned(notice_id, current_user)
    status = 200 if ok else (404 if msg == 'not found' else 403 if msg == 'forbidden' else 400)
    return jsonify({'ok': ok, 'message': msg}), status

@moderator_bp.get('/api/moderator/faqs')
@login_required
@require_role('moderator')
def api_moderator_faqs():
    """Return FAQs in moderator queue (pending + answered for department)."""
    dept = getattr(current_user, 'department', None)
    pending = pending_faqs_for_moderator(dept, current_user)
    from ..services.faq_service import answered_faqs
    answered = answered_faqs()
    # Filter answered by department if target_department is set or include all
    def in_dept(f):
        td = getattr(f, 'target_department', None)
        return (td == dept) or (td in [None, '', 'all'])
    answered_filtered = [f for f in answered if in_dept(f)]

    # Visibility rules for moderators: show student-asked FAQs and own-created FAQs only
    def visible_to_me(faq):
        asker = getattr(faq, 'asker', None)
        role = getattr(asker, 'role', None)
        return (role == 'student' or asker is None or getattr(asker, 'id', None) == getattr(current_user, 'id', None))

    def faq_json(f):
        return {
            'id': f.id,
            'question': f.question,
            'answer': f.answer or '',
            'category': getattr(f, 'category', ''),
            'status': getattr(f, 'status', ''),
            'askedBy': (getattr(getattr(f, 'asker', None), 'sign_name', '') or ''),
        }

    # Pending first
    result = [faq_json(f) for f in pending if visible_to_me(f)] + [faq_json(f) for f in answered_filtered if visible_to_me(f)]
    return jsonify({'ok': True, 'faqs': result})

@moderator_bp.get('/api/moderator/faqs/<int:faq_id>')
@login_required
@require_role('moderator')
def api_moderator_faq_detail(faq_id: int):
    f = get_faq(faq_id)
    if not f:
        return jsonify({'ok': False, 'message': 'Not found'}), 404
    data = {
        'id': f.id,
        'question': f.question,
        'answer': f.answer or '',
        'category': getattr(f, 'category', ''),
        'status': getattr(f, 'status', ''),
        'target_department': getattr(f, 'target_department', None),
    }
    return jsonify({'ok': True, 'faq': data})

@moderator_bp.post('/api/moderator/faqs')
@login_required
@require_role('moderator')
def api_moderator_create_faq():
    data = request.get_json(silent=True) or {}
    question = str(data.get('question','')).strip()
    category = str(data.get('category','General')).strip() or 'General'
    target_department = str(data.get('target_department','')).strip() or None
    answer = str(data.get('answer','')).strip()
    if not question:
        return jsonify({'ok': False, 'message': 'Question is required'}), 400
    ok, faq, msg = create_faq(question, category, target_department, current_user)
    # If an answer is provided, immediately answer the FAQ as the moderator
    if ok and faq and answer:
        ok2, msg2 = answer_faq(faq, answer, current_user)
        if not ok2:
            return jsonify({'ok': False, 'id': getattr(faq,'id', None), 'message': msg2}), 400
        return jsonify({'ok': True, 'id': faq.id, 'message': 'created_and_answered'}), 200
    return jsonify({'ok': ok, 'id': getattr(faq,'id', None), 'message': msg}), (200 if ok else 400)

@moderator_bp.post('/api/moderator/faqs/<int:faq_id>/answer')
@login_required
@require_role('moderator')
def api_moderator_answer_faq(faq_id: int):
    f = get_faq(faq_id)
    if not f:
        return jsonify({'ok': False, 'message': 'Not found'}), 404
    answer = str((request.get_json(silent=True) or {}).get('answer', '')).strip()
    if not answer:
        return jsonify({'ok': False, 'message': 'Answer is required'}), 400
    ok, msg = answer_faq(f, answer, current_user)
    status = 200 if ok else 400
    return jsonify({'ok': ok, 'message': msg}), status

@moderator_bp.post('/api/moderator/faqs/<int:faq_id>/delete')
@login_required
@require_role('moderator')
def api_moderator_delete_faq(faq_id: int):
    """Allow moderator to delete FAQs they created. Admin can delete elsewhere."""
    from ..models.faq import FAQ
    f = db.session.get(FAQ, faq_id)
    if not f:
        return jsonify({'ok': False, 'message': 'Not found'}), 404
    # Only allow deletion if this moderator created the FAQ
    if getattr(f, 'asked_by', None) != getattr(current_user, 'id', None):
        return jsonify({'ok': False, 'message': 'forbidden'}), 403
    try:
        db.session.delete(f)
        db.session.commit()
        return jsonify({'ok': True, 'message': 'deleted'})
    except Exception:
        return jsonify({'ok': False, 'message': 'error'}), 500

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

# Aliases for moderator frontend file names used in new pages
@moderator_bp.get('/moderator/moderator_dashboard.html')
@login_required
@require_role('moderator')
def moderator_dashboard_alias():
    return send_from_directory('frontend/moderator', 'dashboard.html')

@moderator_bp.get('/moderator/moderator_notices.html')
@login_required
@require_role('moderator')
def moderator_notices_alias():
    return send_from_directory('frontend/moderator', 'notices.html')

@moderator_bp.get('/moderator/moderator_faq.html')
@login_required
@require_role('moderator')
def moderator_faq_alias():
    return send_from_directory('frontend/moderator', 'faq.html')

@moderator_bp.get('/moderator/login.html')
@login_required
@require_role('moderator')
def moderator_login_alias():
    return send_from_directory('frontend/auth', 'login.html')

@moderator_bp.get('/moderator/notice-create.html')
@login_required
@require_role('moderator')
def moderator_notice_create_alias():
    # Map to legacy Jinja create view to avoid editing new HTML link
    return send_from_directory('frontend/moderator', 'notices.html')
