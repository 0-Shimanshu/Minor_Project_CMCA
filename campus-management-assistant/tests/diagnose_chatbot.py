import os, sys
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from app import create_app
from app.extensions import db
from app.models.logs import SystemLog


def main():
    app = create_app()
    with app.app_context():
        client = app.test_client()
        api_key = os.getenv('GEMINI_API_KEY')
        print('API key present:', bool(api_key))
        r = client.post('/chatbot/query', json={'query': 'Hello'})
        print('HTTP status:', r.status_code)
        try:
            print('Response JSON:', r.get_json())
        except Exception:
            print('No JSON body')
        h = client.get('/chatbot/health')
        print('Health status:', h.status_code)
        try:
            print('Health JSON:', h.get_json())
        except Exception:
            print('No health JSON')
        logs = SystemLog.query.filter_by(module='chatbot').order_by(SystemLog.created_at.desc()).limit(3).all()
        print('Recent chatbot logs:')
        for l in logs:
            print('-', l.created_at, l.message)

if __name__ == '__main__':
    main()
