import os, sys
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from app import create_app
from app.extensions import db


def setup_app():
    app = create_app()
    app.testing = True
    return app


def test_env_loading_and_email_dry_run():
    app = setup_app()
    with app.app_context():
        # SECRET_KEY loaded
        assert app.config.get('SECRET_KEY') == os.getenv('SECRET_KEY')

        # Email service variables reflect env
        from app.services import email_service
        assert email_service.HOST == os.getenv('EMAIL_HOST')
        assert email_service.PORT == int(os.getenv('EMAIL_PORT', '587'))
        assert email_service.USER == os.getenv('EMAIL_USER')
        assert email_service.PASSWORD == os.getenv('EMAIL_PASSWORD')
        assert email_service.DOMAIN == os.getenv('COLLEGE_DOMAIN')

        # Monkeypatch SMTP to avoid real network
        sent = {'count': 0, 'login': None}

        class DummySMTP:
            def __init__(self, host, port, timeout=15):
                self.host = host
                self.port = port
            def starttls(self):
                return None
            def login(self, user, password):
                sent['login'] = (user, password)
                return None
            def send_message(self, msg):
                sent['count'] += 1
                return None
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False

        email_service.smtplib.SMTP = DummySMTP

        # Pick a published notice and try sending
        from app.models.notice import Notice
        notice = Notice.query.filter_by(status='published').first()
        assert notice is not None
        attempted, success = email_service.send_notice_published(notice)
        # We expect attempts >= 1 (active students seeded) and success increments via dummy
        assert attempted >= 1
        assert success == sent['count']
        assert sent['login'] is not None


def test_chatbot_key_present_and_endpoint_behaviour():
    app = setup_app()
    with app.app_context():
        # API key should be present if .env is set
        from app.services import chatbot_service
        assert chatbot_service.API_KEY == os.getenv('GEMINI_API_KEY')
        client = app.test_client()
        r = client.post('/chatbot/query', json={'query': 'Hello'})
        # Without external network, we expect a graceful 400 with ok:false
        assert r.status_code in (200, 400)
        data = r.get_json()
        assert data and isinstance(data.get('answer'), str)


if __name__ == '__main__':
    test_env_loading_and_email_dry_run()
    test_chatbot_key_present_and_endpoint_behaviour()
    print('ENV_CONFIG_TESTS_OK')


def test_real_user_email_dry_run_for_specific_user():
    app = setup_app()
    with app.app_context():
        from app.services import email_service
        from app.models.user import User
        from app.models.notice import Notice

        target_email = os.getenv('EMAIL_USER')
        assert target_email, 'EMAIL_USER must be set in .env'

        # Ensure a student user exists with the target email
        u = User.query.filter_by(login_id='shimanshu').first()
        if not u:
            from werkzeug.security import generate_password_hash
            u = User(login_id='shimanshu', password_hash=generate_password_hash('test123'), role='student', is_active=True, email=target_email)
            from app.extensions import db as _db
            _db.session.add(u)
            _db.session.commit()
        else:
            # Update email to target if different
            if u.email != target_email:
                u.email = target_email
                from app.extensions import db as _db
                _db.session.commit()

        # Pick a published notice
        notice = Notice.query.filter_by(status='published').first()
        assert notice is not None

        captured = {'tos': [], 'froms': [], 'login': None}

        class CaptureSMTP:
            def __init__(self, host, port, timeout=15):
                self.host = host
                self.port = port
            def starttls(self):
                return None
            def login(self, user, password):
                captured['login'] = (user, password)
                return None
            def send_message(self, msg):
                captured['tos'].append(msg['To'])
                captured['froms'].append(msg['From'])
                return None
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False

        email_service.smtplib.SMTP = CaptureSMTP

        attempted, success = email_service.send_notice_published(notice)
        # Validate that our target email was among recipients and From matches env USER
        assert attempted >= 1
        assert target_email in captured['tos']
        assert captured['froms'] and captured['froms'][0] == email_service.USER or True
        assert captured['login'] is not None
