import os, sys
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.notice import Notice
from app.models.notice_file import NoticeFile
from app.models.logs import SystemLog

"""
Moderator/Admin tests:
- Moderator: create -> edit -> delete notice flow
- Guest: restricted file download logs forbidden attempt
- Admin: access logs page
"""

def setup_app():
    app = create_app()
    app.testing = True
    return app


def test_moderator_crud_and_logs():
    app = setup_app()
    with app.app_context():
        client = app.test_client()
        mod = User.query.filter_by(login_id='mod1').first()
        assert mod is not None

        # Login moderator
        r = client.post('/auth/login', data={'login_id': 'mod1', 'password': 'mod123'}, follow_redirects=True)
        assert r.status_code == 200

        # Create a student-visible notice
        r = client.post('/moderator/notices/create', data={
            'title': 'Route Test Notice',
            'summary': 'Created via tests',
            'content': 'Initial content',
            'category': 'General',
            'visibility': 'student',
        }, follow_redirects=True)
        assert r.status_code == 200

        # Fetch created notice
        created = Notice.query.filter_by(title='Route Test Notice', created_by=mod.id).first()
        assert created is not None

        # Edit notice
        r = client.post(f'/moderator/notices/{created.id}/edit', data={
            'title': 'Route Test Notice Edited',
            'summary': 'Edited',
            'content': 'Edited content',
        }, follow_redirects=True)
        assert r.status_code == 200
        edited = db.session.get(Notice, created.id)
        assert edited.title == 'Route Test Notice Edited'

        # Delete notice
        r = client.post(f'/moderator/notices/{created.id}/delete', follow_redirects=True)
        assert r.status_code == 200
        assert db.session.get(Notice, created.id) is None

        # Logout moderator
        client.get('/auth/logout')

        # Guest attempts restricted download (should be 403 and logged)
        restr = Notice.query.filter_by(title='Restricted Notice').first()
        if restr:
            rfile = NoticeFile.query.filter_by(notice_id=restr.id).first()
            if rfile:
                before = SystemLog.query.filter_by(module='files').count()
                r = client.get(f'/files/notice/{rfile.id}')
                assert r.status_code == 403
                after = SystemLog.query.filter_by(module='files').count()
                assert after >= before + 1


def test_admin_logs_page():
    app = setup_app()
    with app.app_context():
        client = app.test_client()
        # Login as default admin
        r = client.post('/auth/login', data={'login_id': 'admin', 'password': 'admin123'}, follow_redirects=True)
        assert r.status_code == 200
        # Access logs page
        r = client.get('/admin/logs')
        assert r.status_code == 200
        # Expect some system log entries exist (from earlier actions)
        assert b'System Logs' in r.data or b'system' in r.data
        # Access notices list and check seeded titles present
        r = client.get('/admin/notices')
        assert r.status_code == 200
        assert b'Public Notice' in r.data or b'Student Notice' in r.data or b'Restricted Notice' in r.data
        # Logout
        client.get('/auth/logout')

if __name__ == '__main__':
    test_moderator_crud_and_logs()
    test_admin_logs_page()
    print('MOD_ADMIN_TESTS_OK')
