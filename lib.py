import sqlite3
from datetime import datetime, date
db_path = "books.db"

def get_conn():
    return sqlite3.connect(db_path)

def load_books_into_session(st):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, title, author, read_on, rating, created_at FROM books ORDER BY id"
    ).fetchall()
    conn.close()
    st.session_state.books = [
        dict(zip(["id", "title", "author", "read_on", "rating", "created_at"], row)) for row in rows
    ]

def _parse_date(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None

def filter_books(books, title_kw="", author_kw="", rating_min=0, rating_max=5,
                 use_date=False, start=None, end=None):
    rows = []
    tkw = (title_kw or "").strip().lower()
    akw = (author_kw or "").strip().lower()
    for b in books:
        title = str(b.get("title", ""))
        author = str(b.get("author", ""))
        rating = b.get("rating", None)
        d = _parse_date(b.get("read_on"))

        if tkw and tkw not in title.lower():
            continue
        if akw and akw not in author.lower():
            continue
        if rating is not None:
            try:
                r = float(rating)
                if not (rating_min <= r <= rating_max):
                    continue
            except Exception:
                pass
        if use_date:
            if start and d and d < start:
                continue
            if end and d and d > end:
                continue
        rows.append(b)
    return rows