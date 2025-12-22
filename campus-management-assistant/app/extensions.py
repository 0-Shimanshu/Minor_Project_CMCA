from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Shared extensions

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
	# Import locally to avoid circular import
	from .models.user import User
	try:
		return db.session.get(User, int(user_id))
	except Exception:
		return None
