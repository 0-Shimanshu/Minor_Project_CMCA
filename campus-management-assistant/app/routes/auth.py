from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user
from ..services.auth_service import register_student, authenticate

auth_bp = Blueprint('auth', __name__)


@auth_bp.get('/login')
def login():
    return render_template('auth/login.html')


@auth_bp.post('/login')
def login_post():
    login_id = request.form.get('login_id', '').strip()
    password = request.form.get('password', '')
    user, msg = authenticate(login_id, password)
    if not user:
        return render_template('auth/login.html', error=msg), 401
    login_user(user)
    # Role-based redirects
    if user.role == 'admin':
        return redirect('/admin/dashboard')
    if user.role == 'moderator':
        return redirect('/moderator/dashboard')
    if user.role == 'student':
        return redirect('/student/dashboard')
    # Fallback
    return redirect(url_for('auth.login'))


@auth_bp.get('/register')
def register():
    # Student registration only
    return render_template('auth/register.html')


@auth_bp.post('/register')
def register_post():
    sign_name = request.form.get('sign_name', '').strip()
    enrollment_no = request.form.get('enrollment_no', '').strip()
    department = request.form.get('department', '').strip()
    year_str = request.form.get('year', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    try:
        year = int(year_str) if year_str else None
    except ValueError:
        year = None

    ok, msg = register_student(sign_name, enrollment_no, department, year or 0, email, password)
    if not ok:
        return render_template('auth/register.html', error=msg), 400
    return redirect(url_for('auth.login'))


@auth_bp.get('/logout')
def logout():
    logout_user()
    # Spec: redirect to guest home page (placeholder '/')
    return redirect('/')
