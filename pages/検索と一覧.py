import streamlit as st
import pandas as pd
from utils_auth import gate
from datetime import datetime
from lib import load_books_into_session, filter_books
from lib_db import get_conn
import uuid

gate()

st.title("🔍検索と一覧")

if "books" not in st.session_state:
    st.session_state.books = []
    load_books_into_session(st)

st.subheader("検索条件")
title_kw = st.text_input("タイトルキーワード")
author_kw = st.text_input("著者キーワード")
rating_min = st.number_input("最小評価", min_value=0, max_value=5, value=0)
rating_max = st.number_input("最大評価", min_value=0, max_value=5, value=5)
use_date = st.checkbox("読了日で絞り込む")
start = st.date_input("開始日") if use_date else None
end = st.date_input("終了日") if use_date else None

if title_kw or author_kw or rating_min > 0 or rating_max < 5 or use_date:
    books_to_show = filter_books(
        st.session_state.books,
        title_kw=title_kw,
        author_kw=author_kw,
        rating_min=rating_min,
        rating_max=rating_max,
        use_date=use_date,
        start=start,
        end=end
    )
else:
    books_to_show = st.session_state.books



df = pd.DataFrame(books_to_show)

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

st.caption(f"表示冊数 {len(books_to_show)} 冊")

st.subheader("削除")
if st.session_state.books:
    no_max = len(st.session_state.books)
    no_to_delete = st.number_input("削除したい本の『No.』を入力", min_value=1, max_value=no_max, step=1)
    if st.button("No.で削除", key="delete_by_no"):
        idx = int(no_to_delete) - 1
        db_id = books_to_show[idx]["id"]

        with get_conn() as conn:
            conn.execute("DELETE FROM books WHERE id = ?", (db_id,))
            conn.commit()
        load_books_into_session(st)
        st.success(f"No.{no_to_delete}を削除しました。")

options = [(i+1, book["id"], book["title"]) for i, book in enumerate(books_to_show)]
selected = None
delete_id = None
if options:
    selected = st.selectbox(
    "削除する本を選んでください(現在の表示に対応)",
    options,
    format_func=lambda x: f"No.{x[0]} | {x[2]}"
    )
    delete_id = selected[1]


if st.button("選んだ本を削除", key="delete_by_select"):
    if delete_id is None:
        st.warning("本が選択されていません。")
    else:
        _, _, selected_title = selected
        with get_conn() as conn:
            conn.execute("DELETE FROM books WHERE id = ?", (delete_id,))
        load_books_into_session(st)
        st.success(f"『{selected_title}』を削除しました")
elif not options:
    st.info("現在の表示に該当する本がありません。検索条件を変えてみてください。")

