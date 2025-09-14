import streamlit as st
import pandas as pd
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

def load_books():
    rows = conn.execute(
        "SELECT id, title, author, read_on, rating, created_at FROM books ORDER BY id"
    ).fetchall()
    st.session_state.books = [
        dict(zip(["id", "title", "author", "read_on", "rating", "created_at"], row)) for row in rows
    ]

if "books" not in st.session_state:
    st.session_state.books = []
load_books()

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
        
        load_books()
        st.success(f"追加しました:{title}")

df = pd.DataFrame(st.session_state.books)

if df.empty:
    st.info("まだ本が登録されていません。")
else:
    df_display = df.copy()
    df_display.insert(0, "No.", range(1, len(df_display) + 1))
    df_display = df_display.drop(columns=["id"])
    st.dataframe(df_display, use_container_width=True, hide_index=True, 
                 column_config={
                     "title": "タイトル", 
                     "author": "著者", 
                     "read_on": "読了日", 
                     "rating": "評価", 
                     "created_at": "登録日"
                     })
                     
st.subheader("検索・絞り込み")

title_kw = st.text_input("タイトルキーワード")
author_kw = st.text_input("著者キーワード")
rating_min = st.number_input("最小評価", min_value=0, max_value=5, value=0)
rating_max = st.number_input("最大評価", min_value=0, max_value=5, value=5)
use_date = st.checkbox("日付で絞り込む")
start = st.date_input("開始日") if use_date else None
end = st.date_input("終了日") if use_date else None

filtered_books = filter_books(
    st.session_state.books,
    title_kw=title_kw,
    author_kw=author_kw,
    rating_min=rating_min,
    rating_max=rating_max,
    use_date=use_date,
    start=start,
    end=end
)

st.dataframe(filtered_books)

st.subheader("削除")
if st.session_state.books:
    no_max = len(st.session_state.books)
    no_to_delete = st.number_input("削除したい本の『No.』を入力", min_value=1, max_value=no_max, step=1)
    if st.button("No.で削除"):
        idx = int(no_to_delete) - 1
        db_id = st.session_state.books[idx]["id"]
        conn.execute("DELETE FROM books WHERE id = ?", (db_id,))
        conn.commit()
        load_books()
        st.success(f"No.{no_to_delete}を削除しました。")

options = [(i+1, book["id"], book["title"]) for i, book in enumerate(st.session_state.books)]
selected = st.selectbox(
    "削除する本を選んでください",
    options,
    format_func=lambda x: f"No.{x[0]} | {x[2]}"
)
delete_id = selected[1] if selected else None


if st.button("選んだ本を削除"):
    if delete_id is None:
        st.warning("本が選択されていません。")
    else:
        _, _, selected_title = selected
        conn.execute("DELETE FROM books WHERE id = ?", (delete_id,))
        conn.commit()
        load_books()
        st.success(f"『{selected_title}』を削除しました")
