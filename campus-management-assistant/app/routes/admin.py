from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from . import require_role
from ..extensions import db
from ..services.notice_service import admin_all_notices, recent_published_notices, create_notice, update_notice, publish_notice, delete_notice_owned, attach_file
from ..services.faq_service import all_faqs_admin, recent_answered_faqs, create_faq, answer_faq, get_faq
from ..services import get_system_logs, get_email_logs
from ..services.auth_service import list_all_users, set_user_active, delete_user, create_moderator

admin_bp = Blueprint('admin', __name__)


@admin_bp.get('/admin/dashboard')
@login_required
@require_role('admin')
def dashboard():
    notices = recent_published_notices()
    faqs = recent_answered_faqs()
    email_logs = get_email_logs(10)
    return render_template('admin/dashboard.html', notices=notices, faqs=faqs, email_logs=email_logs)


@admin_bp.get('/admin/notices')
@login_required
@require_role('admin')
def notices():
    items = admin_all_notices()
    return render_template('admin/notices.html', notices=items)

@admin_bp.get('/admin/notices/<int:notice_id>')
@login_required
@require_role('admin')
def notice_detail(notice_id: int):
    from ..models.notice import Notice
    n = db.session.get(Notice, notice_id)
    return render_template('admin/notice_detail.html', notice=n)

@admin_bp.get('/admin/notices/create')
@login_required
@require_role('admin')
def notices_create():
    return render_template('admin/notice_create.html')

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
    return render_template('admin/notice_edit.html', notice=n, notice_id=notice_id)

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
    items = all_faqs_admin()
    return render_template('admin/faq.html', faqs=items)

@admin_bp.get('/admin/faq/<int:faq_id>')
@login_required
@require_role('admin')
def faq_detail(faq_id: int):
    f = get_faq(faq_id)
    return render_template('admin/faq_detail.html', faq=f)

@admin_bp.get('/admin/faq/create')
@login_required
@require_role('admin')
def faq_create():
    return render_template('admin/faq_create.html')

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
    return render_template('moderator/faq_answer.html', faq=f)

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
    sys_logs = get_system_logs()
    email_logs = get_email_logs()
    return render_template('admin/logs.html', system_logs=sys_logs, email_logs=email_logs)


@admin_bp.get('/admin/users')
@login_required
@require_role('admin')
def users():
    items = list_all_users()
    return render_template('admin/users.html', users=items)


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
