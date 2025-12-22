import subprocess, sys, os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PY = os.path.join(BASE, 'venv', 'Scripts', 'python.exe')

if __name__ == '__main__':
    print('Seeding dataset...')
    code = subprocess.call([PY, os.path.join(BASE, 'tests', 'seed_data.py')])
    if code != 0:
        print('Seed failed')
        sys.exit(code)
    print('Running route tests...')
    code = subprocess.call([PY, os.path.join(BASE, 'tests', 'test_routes.py')])
    if code != 0:
        sys.exit(code)
    print('Running moderator/admin tests...')
    code = subprocess.call([PY, os.path.join(BASE, 'tests', 'test_moderator_admin.py')])
    if code != 0:
        sys.exit(code)
    print('Running admin/users/scraper/auth tests...')
    code = subprocess.call([PY, os.path.join(BASE, 'tests', 'test_admin_users_scraper_auth.py')])
    sys.exit(code)
