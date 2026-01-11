import streamlit as st
import pandas as pd
from utils_auth import gate
from lib_db import prepare_db, get_conn
from lib import load_books_into_session
from datetime import date, datetime

st.set_page_config(page_title="読書記録アプリ", page_icon="📚")

gate()

prepare_db()

with get_conn() as conn:
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


st.title("📚読書記録アプリ(シンプル版)")

if "books" not in st.session_state:
    st.session_state.books = []
load_books_into_session(st)



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
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO books (title, author, read_on, rating, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                title.strip(), 
                author.strip() or None,
                read_on.isoformat() if isinstance(read_on, date) else None,
                int(rating), 
                datetime.now().isoformat(timespec="seconds"),
                )
            )
        load_books_into_session(st)
        st.success(f"追加しました:{title}")



