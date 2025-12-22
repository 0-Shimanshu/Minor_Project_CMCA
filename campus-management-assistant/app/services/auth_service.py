from typing import Optional, Tuple
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..models.user import User
from ..models.logs import SystemLog


def register_student(sign_name: str, enrollment_no: str, department: str, year: int, email: str, password: str) -> Tuple[bool, str]:
    try:
        # login_id = enrollment number (full)
        login_id = enrollment_no
        # Check duplicates
        if User.query.filter((User.login_id == login_id) | (User.enrollment_no == enrollment_no)).first():
            return False, 'Enrollment already registered'
        # Basic email validation
        email = (email or '').strip()
        if not email or '@' not in email:
            return False, 'Valid email is required'
        user = User()
        user.login_id = login_id
        user.password_hash = generate_password_hash(password)
        user.role = 'student'
        user.enrollment_no = enrollment_no
        user.department = department
        user.year = year
        user.sign_name = sign_name
        user.email = email
        db.session.add(user)
        db.session.commit()
        return True, 'Registered successfully'
    except Exception as e:
        log = SystemLog()
        log.module = 'auth'
        log.message = f'register error: {e}'
        db.session.add(log)
        db.session.commit()
        return False, 'Registration failed'


def authenticate(login_id: str, password: str) -> Tuple[Optional[User], str]:
    try:
        user = User.query.filter_by(login_id=login_id).first()
        if not user:
            db.session.add(SystemLog(module='auth', message=f'login failed: user not found login_id={login_id}'))
            db.session.commit()
            return None, 'Invalid credentials'
        if not user.is_active:
            db.session.add(SystemLog(module='auth', message=f'login failed: user deactivated login_id={login_id}'))
            db.session.commit()
            return None, 'Account deactivated'
        if not check_password_hash(user.password_hash, password):
            db.session.add(SystemLog(module='auth', message=f'login failed: bad password login_id={login_id}'))
            db.session.commit()
            return None, 'Invalid credentials'
        return user, 'Login successful'
    except Exception as e:
        db.session.add(SystemLog(module='auth', message=f'login error: {e} login_id={login_id}'))
        db.session.commit()
        return None, 'Login error'


# Admin user management helpers (service-layer only)
def list_all_users():
    try:
        return User.query.order_by(User.role.asc(), User.created_at.desc()).all()
    except Exception as e:
        log = SystemLog()
        log.module = 'admin'
        log.message = f'user list error: {e}'
        db.session.add(log)
        db.session.commit()
        return []


def list_students(search_enrollment: str = None):
    try:
        q = User.query.filter_by(role='student')
        if search_enrollment:
            like = f"%{search_enrollment}%"
            q = q.filter(User.enrollment_no.ilike(like))
        return q.order_by(User.created_at.desc()).all()
    except Exception as e:
        db.session.add(SystemLog(module='admin', message=f'student list error: {e}'))
        db.session.commit()
        return []


def list_moderators(search_login: str = None):
    try:
        q = User.query.filter_by(role='moderator')
        if search_login:
            like = f"%{search_login}%"
            q = q.filter(User.login_id.ilike(like))
        return q.order_by(User.created_at.desc()).all()
    except Exception as e:
        db.session.add(SystemLog(module='admin', message=f'moderator list error: {e}'))
        db.session.commit()
        return []


def set_user_active(user_id: int, active: bool) -> bool:
    try:
        # Update without attribute assignment to satisfy static analyzer
        q = User.query.filter_by(id=user_id)
        u = q.first()
        if not u:
            return False
        action = 'activate' if active else 'deactivate'
        q.update({"is_active": bool(active)})
        log = SystemLog()
        log.module = 'admin'
        log.message = f'user {action}: {u.login_id}'
        db.session.add(log)
        db.session.commit()
        return True
    except Exception as e:
        log = SystemLog()
        log.module = 'admin'
        log.message = f'user active toggle error: {e}'
        db.session.add(log)
        db.session.commit()
        return False


def delete_user(user_id: int) -> bool:
    try:
        u = db.session.get(User, user_id)
        if not u:
            return False
        login_id = u.login_id
        db.session.delete(u)
        log = SystemLog()
        log.module = 'admin'
        log.message = f'user delete: {login_id}'
        db.session.add(log)
        db.session.commit()
        return True
    except Exception as e:
        log = SystemLog()
        log.module = 'admin'
        log.message = f'user delete error: {e}'
        db.session.add(log)
        db.session.commit()
        return False


def create_moderator(login_id: str, sign_name: str, department: str, email: str, password: str) -> Tuple[bool, str]:
    """Create a moderator account. Admin-only usage via routes.

    Required: unique login_id, non-empty password, basic email format, department for filtering.
    """
    try:
        login_id = (login_id or '').strip()
        sign_name = (sign_name or '').strip()
        department = (department or '').strip()
        email = (email or '').strip()
        password = password or ''
        if not login_id or not password or not sign_name or not department:
            return False, 'All fields are required'
        if '@' not in email:
            return False, 'Valid email is required'
        if User.query.filter_by(login_id=login_id).first():
            return False, 'Login ID already exists'
        u = User(
            login_id=login_id,
            password_hash=generate_password_hash(password),
            role='moderator',
            department=department,
            sign_name=sign_name,
            email=email,
            is_active=True,
        )
        db.session.add(u)
        db.session.commit()
        return True, 'Moderator created'
    except Exception as e:
        db.session.add(SystemLog(module='admin', message=f'moderator create error: {e}'))
        db.session.commit()
        return False, 'Creation failed'
