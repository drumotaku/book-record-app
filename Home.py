import streamlit as st
import pandas as pd
from utils_auth import gate
from lib_db import prepare_db, get_conn
from lib import load_books_into_session, init_share_schema
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

with get_conn() as conn:
    init_share_schema(conn)

st.title("📚読書記録アプリ(シンプル版)")

share_token = st.query_params.get("share") or st.query_params.get("token")
if share_token:
    st.title("📚共有された本のリスト")
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT b.id, b.title, b.author, b.read_on, b.rating, b.created_at,
            COALESCE(sl.title, '') AS share_title
            FROM share_items AS si
            JOIN share_links AS sl ON sl.token = si.token
            JOIN books AS b        ON b.id = si.book_id
            WHERE si.token = ?
                AND COALESCE(sl.is_revoked, 0) = 0
            ORDER BY b.created_at DESC
            """,
            (share_token,),
        ).fetchall()

    if rows:
        share_title = rows[0][-1]
        if share_title:
            st.subheader(share_title)

        cols = ["id", "タイトル", "著者", "読了日", "評価", "登録日", "share_title"]
        df = pd.DataFrame(rows, columns=cols).drop(columns=["share_title"])
        df_display = df.copy()
        df_display.insert(0, "No.", range(1, len(df_display) + 1))
        df_display = df_display.drop(columns=["id"])
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("この共有リンクには本がありません、または無効化されています。")
    
    st.caption(f"トークン:{share_token}")
    st.stop()


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



