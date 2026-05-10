import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "news.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_id TEXT UNIQUE,
            week_label TEXT,
            keyword TEXT,
            title TEXT NOT NULL,
            publish_time TEXT,
            content_snippet TEXT,
            source TEXT,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_week ON news(week_label)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_keyword ON news(keyword)')
    conn.commit()
    conn.close()


def make_unique_id(title, url):
    return hashlib.md5((title + url).encode()).hexdigest()


def save_news_items(items):
    if not items:
        return 0
    conn = get_connection()
    saved = 0
    for item in items:
        uid = make_unique_id(item.title, item.url)
        try:
            conn.execute(
                'INSERT OR IGNORE INTO news (unique_id, week_label, keyword, title, publish_time, content_snippet, source, url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (uid, _week_label(item.publish_time), item.keyword, item.title, item.publish_time, item.content_snippet, item.source, item.url)
            )
            saved += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    return saved


def query_week(week_label):
    conn = get_connection()
    rows = conn.execute(
        'SELECT keyword, title, publish_time, source, url FROM news WHERE week_label = ? ORDER BY keyword, publish_time DESC',
        (week_label,)
    ).fetchall()
    conn.close()
    return rows


def _week_label(date_str):
    if not date_str:
        return ""
    from datetime import datetime
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        year, week, _ = dt.isocalendar()
        return f"{year}-W{week:02d}"
    except (ValueError, TypeError):
        return ""
