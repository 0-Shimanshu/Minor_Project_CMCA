"""
One-time SQLite migration: add 'name' column to 'scraped_websites' if missing.
Safe to run multiple times; no-op if column exists.
"""
import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'database', 'app.db'))

def column_exists(conn, table: str, column: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info('{table}')")
    cols = [row[1] for row in cur.fetchall()]  # row[1] is column name
    return column in cols


def ensure_scraper_name_column():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        if not column_exists(conn, 'scraped_websites', 'name'):
            conn.execute("ALTER TABLE scraped_websites ADD COLUMN name TEXT")
            conn.commit()
            print("Added 'name' column to scraped_websites.")
        else:
            print("Column 'name' already exists; no changes.")
    finally:
        conn.close()


if __name__ == '__main__':
    ensure_scraper_name_column()
