import streamlit as st
import pandas as pd
from datetime import date
from lib import load_books_into_session, filter_books, _parse_date

st.title("🔍検索と一覧")

if "books" not in st.session_state:
    st.session_state.books = []
    load_books_into_session()

st.subheader("検索条件")
title_kw = st.text_input("タイトルキーワード")
author_kw = st.text_input("著者キーワード")
rating_min = st.number_input("最小評価", min_value=0, max_value=5, value=0)
rating_max = st.number_input("最大評価", min_value=0, max_value=5, value=5)
use_date = st.checkbox("日付で絞り込む")
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

st.subheader("本の一覧")

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
