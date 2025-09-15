import streamlit as st
import pandas as pd
from lib import load_books_into_session
from datetime import date, datetime
import sqlite3
conn = sqlite3.connect("books.db")
conn.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    author TEXT,
    read_on TEXT,
    rating INTEGER,
    created_at TEXT
)
""")
conn.commit()

st.set_page_config(page_title="読書記録アプリ", page_icon="📚")
st.title("📚読書記録アプリ(シンプル版)")

if "books" not in st.session_state:
    st.session_state.books = []
load_books_into_session(st)

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

with st.form("add_book", clear_on_submit=True):
    title = st.text_input("タイトル *")
    author = st.text_input("著者")
    read_on = st.date_input("読了日", value=date.today())
    rating = st.slider("評価（１－５）", 1, 5, 3)
    submitted = st.form_submit_button("追加")

if submitted:
    if not title.strip():
        st.warning("タイトルは必須です。")
    else:
        conn.execute(
            "INSERT INTO books (title, author, read_on, rating, created_at) VALUES (?, ?, ?, ?, ?)",
            (title.strip(), 
             author.strip() or None,
             read_on.isoformat() if isinstance(read_on, date) else None,
             int(rating), 
             datetime.now().isoformat(timespec="seconds"),
             )
        )
        conn.commit()
        
        load_books_into_session(st)
        st.success(f"追加しました:{title}")



