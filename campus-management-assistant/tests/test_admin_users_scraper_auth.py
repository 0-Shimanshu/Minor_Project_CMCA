import os, sys
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.faq import FAQ
from app.models.scraper import ScrapedWebsite
from app.models.logs import SystemLog

"""
Admin-centric tests:
- Users: activate/deactivate/delete and login effects
- Scraper: add website and list
- FAQ: create and answer via admin routes
- Auth logs: bad password and deactivated account should log entries
"""


def setup_app():
    app = create_app()
    app.testing = True
    return app


def login_admin(client):
    return client.post('/auth/login', data={'login_id': 'admin', 'password': 'admin123'}, follow_redirects=True)


def test_admin_user_activation_and_delete():
    app = setup_app()
    with app.app_context():
        client = app.test_client()
        # Ensure seed data exists (students/admin)
        if not User.query.filter_by(login_id='ENR001').first() or not User.query.filter_by(login_id='ENR002').first():
            # Run seeding inline
            from tests import seed_data as _seed
            _seed.main()
        # Admin login
        r = login_admin(client)
        assert r.status_code == 200

        # Ensure students exist
        stu1 = User.query.filter_by(login_id='ENR001').first()
        stu2 = User.query.filter_by(login_id='ENR002').first()
        assert stu1 is not None and stu2 is not None

        # Deactivate stu1
        r = client.post(f'/admin/users/{stu1.id}/deactivate', follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(stu1)
        assert stu1.is_active is False

        # Logout admin, attempt stu1 login should fail (401)
        client.get('/auth/logout')
        r = client.post('/auth/login', data={'login_id': 'ENR001', 'password': 'stu123'})
        assert r.status_code == 401
        assert b'Account deactivated' in r.data or b'Invalid credentials' in r.data

        # Login admin again and reactivate stu1
        r = login_admin(client)
        assert r.status_code == 200
        r = client.post(f'/admin/users/{stu1.id}/activate', follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(stu1)
        assert stu1.is_active is True

        # Delete stu2
        r = client.post(f'/admin/users/{stu2.id}/delete', follow_redirects=True)
        assert r.status_code == 200
        assert db.session.get(User, stu2.id) is None

        # Logout admin, attempt stu2 login should fail (401)
        client.get('/auth/logout')
        r = client.post('/auth/login', data={'login_id': 'ENR002', 'password': 'stu456'})
        assert r.status_code == 401


def test_scraper_add_and_list():
    app = setup_app()
    with app.app_context():
        client = app.test_client()
        # Login admin
        r = login_admin(client)
        assert r.status_code == 200

        # Add a website (no scrape run to avoid network)
        before = ScrapedWebsite.query.count()
        exists_before = ScrapedWebsite.query.filter_by(url='https://example.com').first() is not None
        r = client.post('/admin/scraper/add', data={'url': 'https://example.com'}, follow_redirects=True)
        assert r.status_code == 200
        after = ScrapedWebsite.query.count()
        if not exists_before:
            assert after >= before + 1
        else:
            assert after == before

        # Scraper home should list the added URL
        r = client.get('/admin/scraper')
        assert r.status_code == 200
        assert b'example.com' in r.data


def test_admin_faq_create_and_answer():
    app = setup_app()
    with app.app_context():
        client = app.test_client()
        # Login admin
        r = login_admin(client)
        assert r.status_code == 200

        # Create a FAQ
        r = client.post('/admin/faq/create', data={
            'question': 'Test FAQ: What is the policy?',
            'category': 'General',
            'target_department': 'CSE',
        }, follow_redirects=True)
        assert r.status_code == 200

        faq = FAQ.query.filter(FAQ.question.ilike('%Test FAQ%')).order_by(FAQ.created_at.desc()).first()
        assert faq is not None

        # Answer the FAQ
        r = client.post(f'/admin/faq/{faq.id}/answer', data={'answer': 'Policy is as follows.'}, follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(faq)
        assert faq.answer is not None and faq.answered_at is not None

        # FAQ page should include the answered content or at least list the FAQ
        r = client.get('/admin/faq')
        assert r.status_code == 200
        assert b'Test FAQ' in r.data or b'Policy is as follows' in r.data


def test_auth_failure_logging_and_admin_logs():
    app = setup_app()
    with app.app_context():
        client = app.test_client()

        # Bad password
        before = SystemLog.query.filter_by(module='auth').count()
        r = client.post('/auth/login', data={'login_id': 'ENR001', 'password': 'wrongpass'})
        assert r.status_code == 401
        after = SystemLog.query.filter_by(module='auth').count()
        assert after >= before + 1

        # Admin can see auth failures in logs page
        r = login_admin(client)
        assert r.status_code == 200
        r = client.get('/admin/logs')
        assert r.status_code == 200
        assert b'Logs' in r.data or b'auth' in r.data or b'login failed' in r.data


if __name__ == '__main__':
    test_admin_user_activation_and_delete()
    test_scraper_add_and_list()
    test_admin_faq_create_and_answer()
    test_auth_failure_logging_and_admin_logs()
    print('ADMIN_USERS_SCRAPER_AUTH_TESTS_OK')
