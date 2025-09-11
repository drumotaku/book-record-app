import streamlit as st
import pandas as pd
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

def load_books():
    rows = conn.execute(
        "SELECT id, title, author, read_on, rating, created_at FROM books ORDER BY id"
    ).fetchall()
    st.session_state.books = [
        dict(zip(["id", "title", "author", "read_on", "rating", "created_at"], row)) for row in rows
    ]

from datetime import date, datetime

st.set_page_config(page_title="読書記録アプリ", page_icon="📚")
st.title("📚読書記録アプリ(シンプル版)")

if "books" not in st.session_state:
    st.session_state.books = []
load_books()

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
