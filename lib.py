import sqlite3, uuid
from datetime import datetime, timedelta
db_path = "books.db"

def get_conn(db_path="books.db"):
    return sqlite3.connect(db_path, check_same_thread=False)

def init_share_schema(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS share_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE NOT NULL,
        owner_id INTEGER NOT NULL,
        expires_at TEXT,
        is_revoked INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
                       
    CREATE TABLE IF NOT EXISTS share_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT NOT NULL,
        book_id INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_share_items_token ON share_items(token);
    """)
    conn.commit()

def create_share_token(owner_id: int, book_ids: list[int], days: int | None = 7) -> str:
    token = uuid.uuid4().hex
    now = datetime.utcnow()
    expires_at = (now + timedelta(days=days)).isoformat(timespec="seconds") if days else None
    created_at = now.isoformat(timespec="seconds")

    conn = sqlite3.connect("books.db", check_same_thread=False)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO share_links (token, owner_id, expires_at, is_revoked, created_at)
                VALUES (?, ?, ?, 0, ?)
                """,
                (token, owner_id, expires_at, created_at),
            )
            conn.executemany(
                "INSERT INTO share_items (token, book_id) VALUES (?, ?)",
                [(token, bid) for bid in book_ids],
                )
    finally:
        conn.close()
    return token

# lib.py に最下部あたりへ追記

def resolve_share(conn, token: str):
    """token から共有セットの book_id リストを取り出す（期限/失効チェック含む）"""
    cur = conn.cursor()
    row = cur.execute(
        "SELECT expires_at, is_revoked FROM share_links WHERE token = ?",
        (token,)
    ).fetchone()
    if not row:
        return None, "not_found"
    expires_at, is_revoked = row
    if is_revoked:
        return None, "revoked"
    if expires_at:
        try:
            if datetime.utcnow() > datetime.fromisoformat(expires_at):
                return None, "expired"
        except Exception:
            pass
    book_ids = [r[0] for r in cur.execute(
        "SELECT book_id FROM share_items WHERE token = ?",
        (token,)
    ).fetchall()]
    return book_ids, None

def fetch_books_by_ids(conn, ids: list[int]):
    """books から指定IDの本情報をまとめて取得（列名はあなたのスキーマに合わせて）"""
    if not ids:
        return []
    q = ",".join("?" for _ in ids)
    cur = conn.cursor()
    rows = cur.execute(
        f"SELECT id, title, author, read_on, rating, created_at FROM books WHERE id IN ({q})",
        ids
    ).fetchall()
    cols = ["id","title","author","read_on","rating","created_at"]
    return [dict(zip(cols, r)) for r in rows]


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