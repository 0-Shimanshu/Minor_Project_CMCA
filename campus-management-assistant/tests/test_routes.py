import os, sys
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE not in sys.path:
    sys.path.insert(0, BASE)
from app import create_app
from app.extensions import db
from app.models.notice import Notice
from app.models.notice_file import NoticeFile

"""
Route tests using Flask test client (no external services).
- Guest home and notices
- Secure download route (public vs restricted)
- Login as student and access student notice detail
- Chatbot JSON endpoint behavior without API key
"""

def setup_app():
    app = create_app()
    app.testing = True
    return app


def get_ids():
    # Assumes seed_data has created records
    pub_notice = Notice.query.filter_by(title='Public Notice').first()
    restr_notice = Notice.query.filter_by(title='Restricted Notice').first()
    pub_file = NoticeFile.query.filter_by(notice_id=pub_notice.id).first() if pub_notice else None
    restr_file = NoticeFile.query.filter_by(notice_id=restr_notice.id).first() if restr_notice else None
    return pub_notice, pub_file, restr_notice, restr_file


def test_guest_and_downloads():
    app = setup_app()
    with app.app_context():
        client = app.test_client()
        # Home
        r = client.get('/')
        assert r.status_code == 200
        # Public notices page
        r = client.get('/notices')
        assert r.status_code == 200
        pub_notice, pub_file, restr_notice, restr_file = get_ids()
        assert pub_notice is not None and pub_file is not None
        # Public file download should be allowed
        r = client.get(f'/files/notice/{pub_file.id}')
        # Depending on dummy PDF and environment, it should be 200 or 404 if missing; but never 403 for public
        assert r.status_code in (200, 404)
        # Restricted file download should be forbidden to guests
        if restr_file:
            r = client.get(f'/files/notice/{restr_file.id}')
            assert r.status_code == 403


def test_student_detail_and_downloads():
    app = setup_app()
    with app.app_context():
        client = app.test_client()
        # Login as student stu1 (CSE year 2)
        r = client.post('/auth/login', data={'login_id': 'ENR001', 'password': 'stu123'}, follow_redirects=True)
        assert r.status_code == 200
        # Student notices page
        r = client.get('/student/notices')
        assert r.status_code == 200
        # Detail page for restricted notice should be accessible for stu1
        restr_notice = Notice.query.filter_by(title='Restricted Notice').first()
        if restr_notice:
            r = client.get(f'/student/notices/{restr_notice.id}')
            assert r.status_code == 200
            # Download restricted file as student should be allowed
            restr_file = NoticeFile.query.filter_by(notice_id=restr_notice.id).first()
            if restr_file:
                r = client.get(f'/files/notice/{restr_file.id}')
                assert r.status_code in (200, 404)
        # Logout
        client.get('/auth/logout')


def test_chatbot_json_no_key():
    app = setup_app()
    with app.app_context():
        client = app.test_client()
        # Empty query → 400
        r = client.post('/chatbot/query', json={'query': ''})
        assert r.status_code == 400
        # Non-empty when no API key → 400 with friendly message
        r = client.post('/chatbot/query', json={'query': 'Hello'})
        assert r.status_code == 400
        data = r.get_json()
        assert data and data.get('ok') is False and isinstance(data.get('answer'), str)

if __name__ == '__main__':
    # Run tests sequentially
    app = setup_app()
    with app.app_context():
        test_guest_and_downloads()
        test_student_detail_and_downloads()
        test_chatbot_json_no_key()
        print('ROUTE_TESTS_OK')
