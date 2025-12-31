from flask import Flask, send_from_directory
from flask_login import current_user, logout_user
from werkzeug.security import generate_password_hash
from .config import Config, DB_PATH
from .extensions import db, login_manager


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.moderator import moderator_bp
    from app.routes.student import student_bp
    from app.routes.guest import guest_bp
    from app.routes.files import files_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.scraper import scraper_bp

    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(moderator_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(guest_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(scraper_bp)

    # On startup: ensure database exists and default admin user is created
    with app.app_context():
        try:
            import os
            # Ensure database directory exists
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            # Create all tables if missing
            db.create_all()
            # Backfill schema changes: add 'enabled' column to scraped_websites if missing
            try:
                from sqlalchemy import text
                db.session.execute(text("ALTER TABLE scraped_websites ADD COLUMN enabled INTEGER DEFAULT 1"))
                db.session.commit()
            except Exception:
                # Column likely exists or dialect doesn't support this; ignore
                pass
        except Exception:
            pass
        try:
            from .models.user import User
            admin = User.query.filter_by(role='admin').first()
            if not admin:
                login_id = os.getenv('ADMIN_LOGIN_ID', 'admin')
                password = os.getenv('ADMIN_PASSWORD', 'admin123')
                admin_user = User(
                    login_id=login_id,
                    password_hash=generate_password_hash(password),
                    role='admin',
                    is_active=True,
                )
                db.session.add(admin_user)
                db.session.commit()
        except Exception:
            pass

    # Invalidate sessions of deactivated users on next request
    @app.before_request
    def enforce_active_user():
        try:
            if current_user.is_authenticated and not getattr(current_user, 'is_active', True):
                logout_user()
        except Exception:
            pass

    @app.route('/css/<path:filename>')
    def serve_css(filename):
        return send_from_directory('frontend/css', filename)

    @app.route('/js/<path:filename>')
    def serve_js(filename):
        return send_from_directory('frontend/js', filename)

    return app
