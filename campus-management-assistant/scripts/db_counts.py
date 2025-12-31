import os
import json
import sqlite3


def main() -> int:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, 'app', 'database', 'app.db')
    result = {
        'db_path': db_path,
        'exists': os.path.exists(db_path),
        'scraped_websites': 0,
        'scrape_logs': {'count': 0, 'first': None, 'last': None},
        'chatbot_documents': {
            'total': 0,
            'by_source_type': {},
            'scrape_text_total_length': 0,
        },
    }

    if not os.path.exists(db_path):
        print(json.dumps(result))
        return 0

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    def tables() -> set[str]:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return {r['name'] for r in cur.fetchall()}

    tbls = tables()

    if 'scraped_websites' in tbls:
        cur.execute('SELECT COUNT(*) AS c FROM scraped_websites')
        result['scraped_websites'] = cur.fetchone()['c']

    if 'scrape_logs' in tbls:
        cur.execute('SELECT COUNT(*) AS c FROM scrape_logs')
        result['scrape_logs']['count'] = cur.fetchone()['c']
        cur.execute('PRAGMA table_info(scrape_logs)')
        cols = {r[1] for r in cur.fetchall()}
        ts_col = None
        for c in ('created_at', 'timestamp', 'run_at'):
            if c in cols:
                ts_col = c
                break
        if ts_col:
            cur.execute(f'SELECT MIN({ts_col}) AS first, MAX({ts_col}) AS last FROM scrape_logs')
            row = cur.fetchone()
            result['scrape_logs']['first'] = row['first']
            result['scrape_logs']['last'] = row['last']

    if 'chatbot_documents' in tbls:
        cur.execute('SELECT COUNT(*) AS c FROM chatbot_documents')
        result['chatbot_documents']['total'] = cur.fetchone()['c']
        cur.execute("SELECT COALESCE(source_type, 'unknown') AS st, COUNT(*) AS c FROM chatbot_documents GROUP BY COALESCE(source_type, 'unknown') ORDER BY c DESC")
        for r in cur.fetchall():
            result['chatbot_documents']['by_source_type'][r['st']] = r['c']
        cur.execute('PRAGMA table_info(chatbot_documents)')
        ccols = {r[1] for r in cur.fetchall()}
        if 'content' in ccols:
            cur.execute("SELECT COALESCE(SUM(LENGTH(content)), 0) AS total_len FROM chatbot_documents WHERE source_type='scrape_text'")
            row = cur.fetchone()
            result['chatbot_documents']['scrape_text_total_length'] = row['total_len']

    con.close()
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
