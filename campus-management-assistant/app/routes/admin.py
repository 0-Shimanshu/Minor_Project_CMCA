from flask import Blueprint, redirect, url_for, request, flash, jsonify, send_from_directory
from flask_login import login_required, current_user
from . import require_role
from ..extensions import db
from ..services.notice_service import admin_all_notices, recent_published_notices, create_notice, update_notice, publish_notice, delete_notice_owned, attach_file
from ..services.faq_service import all_faqs_admin, recent_answered_faqs, create_faq, answer_faq, get_faq
from ..services import get_system_logs, get_email_logs
from ..services.scraper_service import list_websites, add_website, get_website, scrape_website, list_logs
from ..services.scraper_service import scrape_all
from ..services.auth_service import list_all_users, set_user_active, delete_user, create_moderator
from ..models.notice_file import NoticeFile
import os

admin_bp = Blueprint('admin', __name__)


@admin_bp.get('/admin/dashboard')
@login_required
@require_role('admin')
def dashboard():
    # Serve new frontend admin dashboard (no Jinja)
    return send_from_directory('frontend/admin', 'dashboard.html')


@admin_bp.get('/admin/notices')
@login_required
@require_role('admin')
def notices():
    # Serve new frontend admin notices page (no Jinja)
    return send_from_directory('frontend/admin', 'notices.html')

@admin_bp.get('/admin/notices/<int:notice_id>')
@login_required
@require_role('admin')
def notice_detail(notice_id: int):
    from ..models.notice import Notice
    n = db.session.get(Notice, notice_id)
    return send_from_directory('frontend/admin', 'notices.html')

@admin_bp.get('/admin/notices/create')
@login_required
@require_role('admin')
def notices_create():
    return send_from_directory('frontend/admin', 'notices.html')

@admin_bp.post('/admin/notices/create')
@login_required
@require_role('admin')
def notices_create_post():
    ok, notice, msg = create_notice(
        current_user,
        request.form.get('title','').strip(),
        request.form.get('summary','').strip() or None,
        request.form.get('content','').strip(),
        request.form.get('category','').strip(),
        request.form.get('visibility','').strip(),
        request.form.get('target_department','').strip() or None,
        int(request.form.get('target_year')) if request.form.get('target_year') else None,
    )
    # Optional attachment upload
    file = request.files.get('file')
    if ok and notice and file and file.filename:
        attach_file(notice, file)
    if ok:
        # Optionally publish immediately and notify
        if request.form.get('publish_now') in ['1','on','true','True']:
            notify = (request.form.get('notify') in ['1','on','true','True'])
            publish_notice(notice, send_email=notify)
            flash('Notice created and published', 'success')
        else:
            flash('Notice created', 'success')
    else:
        flash('Failed to create notice', 'error')
    return redirect(url_for('admin.notices'))

@admin_bp.get('/admin/notices/<int:notice_id>/edit')
@login_required
@require_role('admin')
def notices_edit(notice_id: int):
    from ..models.notice import Notice
    n = db.session.get(Notice, notice_id)
    return send_from_directory('frontend/admin', 'notices.html')

@admin_bp.post('/admin/notices/<int:notice_id>/edit')
@login_required
@require_role('admin')
def notices_edit_post(notice_id: int):
    from ..models.notice import Notice
    n = db.session.get(Notice, notice_id)
    if n:
        update_notice(n,
            title=request.form.get('title','').strip(),
            summary=request.form.get('summary','').strip() or None,
            content=request.form.get('content','').strip(),
            visibility=request.form.get('visibility','').strip(),
            target_department=request.form.get('target_department','').strip() or None,
            target_year=int(request.form.get('target_year')) if request.form.get('target_year') else None,
        )
        # Optional new attachment
        file = request.files.get('file')
        if file and file.filename:
            attach_file(n, file)
        flash('Notice updated', 'success')
    return redirect(url_for('admin.notices'))


@admin_bp.post('/admin/notices/<int:notice_id>/attachments/<int:file_id>/delete')
@login_required
@require_role('admin')
def admin_delete_notice_attachment(notice_id: int, file_id: int):
    try:
        from ..models.notice import Notice
        n = db.session.get(Notice, notice_id)
        if not n:
            return jsonify({'ok': False, 'message': 'Notice not found'}), 404
        nf = db.session.get(NoticeFile, file_id)
        if not nf or nf.notice_id != n.id:
            return jsonify({'ok': False, 'message': 'Attachment not found'}), 404
        # Remove file from disk safely
        try:
            if nf.file_path and os.path.exists(nf.file_path):
                os.remove(nf.file_path)
        except Exception:
            pass
        db.session.delete(nf)
        db.session.commit()
        return jsonify({'ok': True, 'message': 'deleted'})
    except Exception:
        return jsonify({'ok': False, 'message': 'error'}), 500

@admin_bp.post('/admin/notices/<int:notice_id>/publish')
@login_required
@require_role('admin')
def notices_publish_post(notice_id: int):
    from ..models.notice import Notice
    n = db.session.get(Notice, notice_id)
    if n:
        notify = (request.form.get('notify') in ['1', 'on', 'true', 'True'])
        publish_notice(n, send_email=notify)
        flash('Notice published', 'success')
    return redirect(url_for('admin.notices'))

@admin_bp.post('/admin/notices/<int:notice_id>/delete')
@login_required
@require_role('admin')
def notices_delete_post_admin(notice_id: int):
    delete_notice_owned(notice_id, current_user)
    flash('Notice deleted', 'success')
    return redirect(url_for('admin.notices'))


@admin_bp.get('/admin/faq')
@login_required
@require_role('admin')
def faq():
    # Serve new frontend admin FAQ page
    return send_from_directory('frontend/admin', 'faq.html')

@admin_bp.get('/admin/faq/<int:faq_id>')
@login_required
@require_role('admin')
def faq_detail(faq_id: int):
    f = get_faq(faq_id)
    return send_from_directory('frontend/admin', 'faq.html')

@admin_bp.get('/admin/faq/create')
@login_required
@require_role('admin')
def faq_create():
    return send_from_directory('frontend/admin', 'faq.html')

@admin_bp.post('/admin/faq/create')
@login_required
@require_role('admin')
def faq_create_post():
    create_faq(
        request.form.get('question','').strip(),
        request.form.get('category','').strip(),
        request.form.get('target_department','').strip() or None,
        current_user,
    )
    flash('FAQ created', 'success')
    return redirect(url_for('admin.faq'))

@admin_bp.get('/admin/faq/<int:faq_id>/answer')
@login_required
@require_role('admin')
def faq_answer_admin(faq_id: int):
    f = get_faq(faq_id)
    return send_from_directory('frontend/admin', 'faq.html')

@admin_bp.post('/admin/faq/<int:faq_id>/answer')
@login_required
@require_role('admin')
def faq_answer_post_admin(faq_id: int):
    f = get_faq(faq_id)
    if f:
        answer_faq(f, request.form.get('answer','').strip(), current_user)
        flash('FAQ answered', 'success')
    return redirect(url_for('admin.faq'))

@admin_bp.post('/admin/faq/<int:faq_id>/delete')
@login_required
@require_role('admin')
def faq_delete_admin(faq_id: int):
    from ..models.faq import FAQ
    f = db.session.get(FAQ, faq_id)
    if f:
        db.session.delete(f)
        db.session.commit()
        flash('FAQ deleted', 'success')
    else:
        flash('FAQ not found', 'error')
    return redirect(url_for('admin.faq'))


@admin_bp.get('/admin/logs')
@login_required
@require_role('admin')
def logs():
    # Serve new frontend admin logs page
    return send_from_directory('frontend/admin', 'logs.html')


@admin_bp.get('/admin/users')
@login_required
@require_role('admin')
def users():
    # Serve new frontend admin users page
    return send_from_directory('frontend/admin', 'users.html')

@admin_bp.get('/api/admin/logs')
@login_required
@require_role('admin')
def api_admin_logs():
    sys_logs = get_system_logs()
    email_logs = get_email_logs()
    def fmt_dt(dt):
        try:
            return dt.strftime('%d %b %Y %H:%M') if dt else ''
        except Exception:
            return ''
    system = [
        {
            'timestamp': fmt_dt(getattr(l, 'created_at', None)),
            'module': getattr(l, 'module', ''),
            'message': getattr(l, 'message', ''),
        } for l in sys_logs
    ]
    emails = [
        {
            'subject': getattr(l, 'subject', ''),
            'to': 'students',
            'status': 'sent',
            'error': '',
            'timestamp': fmt_dt(getattr(l, 'sent_at', None)),
        } for l in email_logs
    ]
    return jsonify({'ok': True, 'system': system, 'emails': emails})

@admin_bp.get('/api/admin/users')
@login_required
@require_role('admin')
def api_admin_users():
    items = list_all_users()
    def user_json(u):
        return {
            'id': getattr(u, 'id', None),
            'login_id': getattr(u, 'login_id', ''),
            'enrollment_no': getattr(u, 'enrollment_no', ''),
            'name': getattr(u, 'sign_name', ''),
            'email': getattr(u, 'email', ''),
            'role': getattr(u, 'role', ''),
            'department': getattr(u, 'department', ''),
            'status': ('active' if getattr(u, 'is_active', True) else 'inactive'),
        }
    return jsonify({'ok': True, 'users': [user_json(u) for u in items]})

@admin_bp.post('/api/admin/users/create-moderator')
@login_required
@require_role('admin')
def api_admin_create_moderator():
    data = request.get_json(silent=True) or {}
    ok, msg = create_moderator(
        login_id=str(data.get('login_id','')).strip(),
        sign_name=str(data.get('sign_name','')).strip(),
        department=str(data.get('department','')).strip(),
        email=str(data.get('email','')).strip(),
        password=str(data.get('password','') or '')
    )
    return jsonify({'ok': ok, 'message': msg}), (200 if ok else 400)

@admin_bp.post('/api/admin/users/<int:user_id>/activate')
@login_required
@require_role('admin')
def api_admin_user_activate(user_id: int):
    try:
        from ..models.user import User
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'ok': False, 'message': 'User not found'}), 404
        set_user_active(user_id, True)
        return jsonify({'ok': True, 'message': 'User activated'})
    except Exception as e:
        return jsonify({'ok': False, 'message': f'Error: {str(e)}'}), 500

@admin_bp.post('/api/admin/users/<int:user_id>/deactivate')
@login_required
@require_role('admin')
def api_admin_user_deactivate(user_id: int):
    try:
        from ..models.user import User
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'ok': False, 'message': 'User not found'}), 404
        if user.id == current_user.id:
            return jsonify({'ok': False, 'message': 'Cannot deactivate yourself'}), 400
        set_user_active(user_id, False)
        return jsonify({'ok': True, 'message': 'User deactivated'})
    except Exception as e:
        return jsonify({'ok': False, 'message': f'Error: {str(e)}'}), 500

@admin_bp.post('/api/admin/users/<int:user_id>/delete')
@login_required
@require_role('admin')
def api_admin_user_delete(user_id: int):
    try:
        from ..models.user import User
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'ok': False, 'message': 'User not found'}), 404
        if user.id == current_user.id:
            return jsonify({'ok': False, 'message': 'Cannot delete yourself'}), 400
        delete_user(user_id)
        return jsonify({'ok': True, 'message': 'User deleted'})
    except Exception as e:
        return jsonify({'ok': False, 'message': f'Error: {str(e)}'}), 500

@admin_bp.get('/api/admin/dashboard')
@login_required
@require_role('admin')
def api_admin_dashboard():
    notices = recent_published_notices()
    faqs = recent_answered_faqs()
    email_logs = get_email_logs(10)

    # Stats: total users, published notices count, answered FAQs count
    try:
        from ..models.user import User
        from ..models.faq import FAQ
        from ..models.notice import Notice
        total_users = User.query.count()
        published_count = Notice.query.filter_by(status='published').count()
        answered_count = FAQ.query.filter_by(status='answered').count()
    except Exception:
        total_users = 0
        published_count = 0
        answered_count = 0

    def fmt_date(dt):
        try:
            return dt.strftime('%d %b %Y') if dt else ''
        except Exception:
            return ''

    notices_json = [
        {
            'id': n.id,
            'title': n.title,
            'category': getattr(getattr(n, 'category', None), 'name', ''),
            'date': fmt_date(getattr(n, 'created_at', None)),
        } for n in notices
    ]
    faqs_json = [
        {
            'id': f.id,
            'question': f.question,
            'answered_at': fmt_date(getattr(f, 'answered_at', None)),
        } for f in faqs
    ]
    emails_json = [
        {
            'subject': getattr(e, 'subject', ''),
            'date': fmt_date(getattr(e, 'sent_at', None)),
        } for e in email_logs
    ]
    user_json = {
        'name': getattr(current_user, 'sign_name', '') or getattr(current_user, 'name', ''),
        'id': getattr(current_user, 'id', None),
        'login_id': getattr(current_user, 'login_id', ''),
        'role': getattr(current_user, 'role', ''),
        'department': getattr(current_user, 'department', ''),
    }
    # My authored notices and answered FAQs
    try:
        from ..models.notice import Notice
        my_notices_q = Notice.query.filter(Notice.created_by == getattr(current_user, 'id', None)).order_by(Notice.created_at.desc()).limit(10)
        recent_my_notices = [
            {
                'id': n.id,
                'title': n.title,
                'category': getattr(getattr(n, 'category', None), 'name', ''),
                'date': fmt_date(getattr(n, 'created_at', None)),
                'status': getattr(n, 'status', ''),
            } for n in my_notices_q
        ]
    except Exception:
        recent_my_notices = []
    try:
        from ..models.faq import FAQ
        my_faqs_q = FAQ.query.filter(FAQ.answered_by == getattr(current_user, 'id', None)).order_by(FAQ.answered_at.desc()).limit(10)
        recent_my_faqs = [
            {
                'id': f.id,
                'question': f.question,
                'answered_at': fmt_date(getattr(f, 'answered_at', None)),
                'category': getattr(f, 'category', ''),
            } for f in my_faqs_q
        ]
    except Exception:
        recent_my_faqs = []

    return jsonify({
        'ok': True,
        'user': user_json,
        'stats': {
            'total_users': total_users,
            'published_notices': published_count,
            'answered_faqs': answered_count,
        },
        'recent_notices': notices_json,
        'recent_faqs': faqs_json,
        'recent_emails': emails_json,
        'recent_my_notices': recent_my_notices,
        'recent_my_faqs': recent_my_faqs,
    })

@admin_bp.get('/api/admin/notices')
@login_required
@require_role('admin')
def api_admin_notices():
    items = admin_all_notices()
    def fmt_date(dt):
        try:
            return dt.strftime('%d %b %Y') if dt else ''
        except Exception:
            return ''
    data = [
        {
            'id': n.id,
            'title': n.title,
            'status': getattr(n, 'status', ''),
            'visibility': getattr(n, 'visibility', ''),
            'category': getattr(getattr(n, 'category', None), 'name', ''),
            'audience': ('All Students' if getattr(n, 'visibility', '') in ['public', 'student'] else f"{getattr(n, 'target_department', '')} · Year {getattr(n, 'target_year', '')}"),
            'created_at': fmt_date(getattr(n, 'created_at', None)),
            'posted_by': (getattr(getattr(n, 'author', None), 'sign_name', '') or ''),
        } for n in items
    ]
    return jsonify({'ok': True, 'notices': data})

@admin_bp.get('/api/admin/notices/<int:notice_id>')
@login_required
@require_role('admin')
def api_admin_notice_detail(notice_id: int):
    from ..models.notice import Notice
    n = db.session.get(Notice, notice_id)
    if not n:
        return jsonify({'ok': False, 'message': 'Not found'}), 404
    def fmt_date(dt):
        try:
            return dt.strftime('%d %b %Y') if dt else ''
        except Exception:
            return ''
    # attachments
    atts = []
    try:
        files = getattr(n, 'files', []) or []
        for f in files:
            atts.append({ 'id': getattr(f, 'id', None), 'name': getattr(f, 'file_name', '') })
    except Exception:
        atts = []
    data = {
        'id': n.id,
        'title': n.title,
        'summary': getattr(n, 'summary', '') or '',
        'content': getattr(n, 'content', '') or '',
        'category': getattr(getattr(n, 'category', None), 'name', ''),
        'status': getattr(n, 'status', ''),
        'visibility': getattr(n, 'visibility', ''),
        'audience': ('All Students' if getattr(n, 'visibility', '') in ['public', 'student'] else f"{getattr(n, 'target_department', '')} · Year {getattr(n, 'target_year', '')}"),
        'date': fmt_date(getattr(n, 'created_at', None)),
        'target_department': getattr(n, 'target_department', '') or '',
        'target_year': getattr(n, 'target_year', None),
        'posted_by': (getattr(getattr(n, 'author', None), 'sign_name', '') or ''),
        'attachments': atts,
    }
    return jsonify({'ok': True, 'notice': data})

@admin_bp.post('/api/admin/notices/<int:notice_id>/publish')
@login_required
@require_role('admin')
def api_admin_publish_notice(notice_id: int):
    from ..models.notice import Notice
    n = db.session.get(Notice, notice_id)
    if not n:
        return jsonify({'ok': False, 'message': 'Not found'}), 404
    notify = (request.args.get('notify') in ['1', 'on', 'true', 'True'])
    ok, msg = publish_notice(n, send_email=notify)
    return jsonify({'ok': ok, 'message': msg}), (200 if ok else 400)

@admin_bp.post('/api/admin/notices/<int:notice_id>/delete')
@login_required
@require_role('admin')
def api_admin_delete_notice(notice_id: int):
    ok, msg = delete_notice_owned(notice_id, current_user)
    status = 200 if ok else (404 if msg == 'not found' else 400)
    return jsonify({'ok': ok, 'message': msg}), status

@admin_bp.get('/api/admin/faqs')
@login_required
@require_role('admin')
def api_admin_faqs():
    items = all_faqs_admin()
    # Sort pending first, then answered
    try:
        items = sorted(items, key=lambda f: (0 if getattr(f, 'status', '') == 'pending' else 1, getattr(f, 'created_at', None) or 0))
    except Exception:
        pass
    def faq_json(f):
        return {
            'id': f.id,
            'question': f.question,
            'answer': f.answer or '',
            'status': getattr(f, 'status', ''),
            'category': getattr(f, 'category', ''),
            'askedBy': (getattr(getattr(f, 'asker', None), 'sign_name', '') or ''),
        }
    return jsonify({'ok': True, 'faqs': [faq_json(f) for f in items]})

@admin_bp.post('/api/admin/faqs/<int:faq_id>/answer')
@login_required
@require_role('admin')
def api_admin_answer_faq(faq_id: int):
    f = get_faq(faq_id)
    if not f:
        return jsonify({'ok': False, 'message': 'Not found'}), 404
    answer = str((request.get_json(silent=True) or {}).get('answer', '')).strip()
    if not answer:
        return jsonify({'ok': False, 'message': 'Answer is required'}), 400
    ok, msg = answer_faq(f, answer, current_user)
    return jsonify({'ok': ok, 'message': msg}), (200 if ok else 400)

@admin_bp.post('/api/admin/faqs/<int:faq_id>/delete')
@login_required
@require_role('admin')
def api_admin_delete_faq(faq_id: int):
    from ..models.faq import FAQ
    f = db.session.get(FAQ, faq_id)
    if not f:
        return jsonify({'ok': False, 'message': 'Not found'}), 404
    db.session.delete(f)
    db.session.commit()
    return jsonify({'ok': True, 'message': 'deleted'})

# Aliases for admin frontend file names used in new pages
@admin_bp.get('/admin/admin_dashboard.html')
@login_required
@require_role('admin')
def admin_dashboard_alias():
    return send_from_directory('frontend/admin', 'dashboard.html')

@admin_bp.get('/admin/admin_notices.html')
@login_required
@require_role('admin')
def admin_notices_alias():
    return send_from_directory('frontend/admin', 'notices.html')

@admin_bp.get('/admin/admin_faq.html')
@login_required
@require_role('admin')
def admin_faq_alias():
    return send_from_directory('frontend/admin', 'faq.html')

@admin_bp.get('/admin/login.html')
@login_required
@require_role('admin')
def admin_login_alias():
    return send_from_directory('frontend/auth', 'login.html')

@admin_bp.get('/admin/scraper')
@login_required
@require_role('admin')
def admin_scraper_page():
    return send_from_directory('frontend/admin', 'scraper.html')

@admin_bp.get('/api/admin/scraper/sites')
@login_required
@require_role('admin')
def api_admin_scraper_sites():
    sites = list_websites()
    data = [
        {
            'id': s.id,
            'name': getattr(s, 'name', '') or '',
            'url': s.url,
            'enabled': bool(getattr(s, 'enabled', True)),
            'added_at': s.added_at.strftime('%d %b %Y %H:%M') if getattr(s, 'added_at', None) else ''
        } for s in sites
    ]
    return jsonify({'ok': True, 'sites': data})

@admin_bp.post('/api/admin/scraper/sites')
@login_required
@require_role('admin')
def api_admin_scraper_add_site():
    payload = (request.get_json(silent=True) or {})
    url = str(payload.get('url','')).strip()
    name = str(payload.get('name','')).strip()  # accepted but not stored yet
    if not url:
        return jsonify({'ok': False, 'message': 'URL required'}), 400
    ok, msg = add_website(url, name=name)
    # Include name now that it's persisted (manual runs only)
    return jsonify({'ok': ok, 'message': msg, 'name': name}), (200 if ok else 400)

@admin_bp.post('/api/admin/scraper/sites/<int:site_id>/run')
@login_required
@require_role('admin')
def api_admin_scraper_run(site_id: int):
    site = get_website(site_id)
    if not site:
        return jsonify({'ok': False, 'message': 'Not found'}), 404
    # Respect enabled flag: do not run when disabled
    if not bool(getattr(site, 'enabled', True)):
        return jsonify({'ok': False, 'status': 'disabled'}), 200
    ok, status = scrape_website(site)
    return jsonify({'ok': ok, 'status': status})

@admin_bp.post('/api/admin/scraper/sites/<int:site_id>/enable')
@login_required
@require_role('admin')
def api_admin_scraper_enable(site_id: int):
    site = get_website(site_id)
    if not site:
        return jsonify({'ok': False, 'message': 'Not found'}), 404
    try:
        site.enabled = True
        db.session.commit()
        return jsonify({'ok': True})
    except Exception:
        return jsonify({'ok': False}), 500

@admin_bp.post('/api/admin/scraper/sites/<int:site_id>/disable')
@login_required
@require_role('admin')
def api_admin_scraper_disable(site_id: int):
    site = get_website(site_id)
    if not site:
        return jsonify({'ok': False, 'message': 'Not found'}), 404
    try:
        site.enabled = False
        db.session.commit()
        return jsonify({'ok': True})
    except Exception:
        return jsonify({'ok': False}), 500

@admin_bp.post('/api/admin/scraper/run-all')
@login_required
@require_role('admin')
def api_admin_scraper_run_all():
    try:
        completed, total = scrape_all()
        return jsonify({'ok': True, 'completed': completed, 'total': total})
    except Exception:
        return jsonify({'ok': False}), 500

@admin_bp.post('/api/admin/scraper/sites/<int:site_id>/delete')
@login_required
@require_role('admin')
def api_admin_scraper_delete(site_id: int):
    site = get_website(site_id)
    if not site:
        return jsonify({'ok': False, 'message': 'Not found'}), 404
    try:
        from ..extensions import db
        db.session.delete(site)
        db.session.commit()
        return jsonify({'ok': True})
    except Exception:
        return jsonify({'ok': False}), 500

@admin_bp.get('/api/admin/scraper/logs')
@login_required
@require_role('admin')
def api_admin_scraper_logs():
    logs = list_logs(100)
    def fmt_dt(dt):
        try:
            return dt.strftime('%d %b %Y %H:%M') if dt else ''
        except Exception:
            return ''
    data = [
        {
            'id': l.id,
            'website_id': l.website_id,
            'status': l.status,
            'extracted_text_length': l.extracted_text_length,
            'pdf_links_found': l.pdf_links_found,
            'scraped_at': fmt_dt(getattr(l, 'scraped_at', None)),
        } for l in logs
    ]
    return jsonify({'ok': True, 'logs': data})

@admin_bp.get('/admin/admin_logs.html')
@login_required
@require_role('admin')
def admin_logs_alias():
    return send_from_directory('frontend/admin', 'logs.html')

@admin_bp.get('/admin/admin_users.html')
@login_required
@require_role('admin')
def admin_users_alias():
    return send_from_directory('frontend/admin', 'users.html')








@admin_bp.post('/admin/users/create-moderator')
@login_required
@require_role('admin')
def users_create_moderator():
    ok, msg = create_moderator(
        login_id=request.form.get('login_id','').strip(),
        sign_name=request.form.get('sign_name','').strip(),
        department=request.form.get('department','').strip(),
        email=request.form.get('email','').strip(),
        password=request.form.get('password','') or ''
    )
    flash(msg, 'success' if ok else 'error')
    # Stay on dashboard to keep UX tight
    return redirect(url_for('admin.dashboard'))


@admin_bp.post('/admin/users/<int:user_id>/activate')
@login_required
@require_role('admin')
def user_activate(user_id: int):
    set_user_active(user_id, True)
    return redirect(url_for('admin.users'))


@admin_bp.post('/admin/users/<int:user_id>/deactivate')
@login_required
@require_role('admin')
def user_deactivate(user_id: int):
    set_user_active(user_id, False)
    return redirect(url_for('admin.users'))


@admin_bp.post('/admin/users/<int:user_id>/delete')
@login_required
@require_role('admin')
def user_delete(user_id: int):
    delete_user(user_id)
    return redirect(url_for('admin.users'))


# Purge all non-admin users safely
@admin_bp.post('/api/admin/users/purge-non-admins')
@login_required
@require_role('admin')
def api_admin_purge_non_admins():
    try:
        from ..models.user import User
        from ..models.notice import Notice
        from ..models.faq import FAQ
        from ..models.logs import EmailLog

        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            return jsonify({'ok': False, 'message': 'Admin user not found'}), 400

        # Reassign notices authored by non-admins to admin
        try:
            from sqlalchemy import and_
            reassign_count = 0
            non_admin_notice_authors = db.session.query(Notice).join(User, Notice.created_by == User.id).filter(User.role != 'admin').all()
            for n in non_admin_notice_authors:
                n.created_by = admin_user.id
                reassign_count += 1
        except Exception:
            reassign_count = 0

        # Null out FAQ asker/answerer if non-admin
        faq_updates = 0
        try:
            faqs = FAQ.query.all()
            for f in faqs:
                if f.asked_by:
                    u = db.session.get(User, f.asked_by)
                    if u and u.role != 'admin':
                        f.asked_by = None
                        faq_updates += 1
                if f.answered_by:
                    u2 = db.session.get(User, f.answered_by)
                    if u2 and u2.role != 'admin':
                        f.answered_by = None
                        faq_updates += 1
        except Exception:
            pass

        # Reassign EmailLog.sent_by from non-admin to admin
        email_updates = 0
        try:
            emails = EmailLog.query.all()
            for e in emails:
                if e.sent_by:
                    u = db.session.get(User, e.sent_by)
                    if u and u.role != 'admin':
                        e.sent_by = admin_user.id
                        email_updates += 1
        except Exception:
            pass

        # Delete all non-admin users
        try:
            non_admins = User.query.filter(User.role != 'admin').all()
            deleted = 0
            for u in non_admins:
                db.session.delete(u)
                deleted += 1
        except Exception:
            return jsonify({'ok': False, 'message': 'Failed to collect non-admin users'}), 500

        db.session.commit()
        return jsonify({
            'ok': True,
            'message': 'Purged non-admin users',
            'reassigned_notices': reassign_count,
            'updated_faq_links': faq_updates,
            'updated_email_logs': email_updates,
            'deleted_users': deleted,
        })
    except Exception as e:
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'ok': False, 'message': f'Error: {str(e)}'}), 500
