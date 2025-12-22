from flask import redirect, url_for, flash
from flask_login import login_required, current_user
from ..extensions import db
from ..models.logs import SystemLog


def require_role(role: str):
	def decorator(fn):
		from functools import wraps
		@wraps(fn)
		def wrapper(*args, **kwargs):
			if not current_user.is_authenticated:
				flash('Please log in to continue.')
				return redirect(url_for('auth.login'))
			if getattr(current_user, 'role', None) != role:
				try:
					db.session.add(SystemLog(module='auth', message=f'role violation: needed {role}'))
					db.session.commit()
				except Exception:
					pass
				flash('You are not authorized to access this page.')
				return redirect(url_for('auth.login'))
			return fn(*args, **kwargs)
		return wrapper
	return decorator

