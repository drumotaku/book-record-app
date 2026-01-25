import streamlit as st
import pandas as pd
from utils_auth import gate
from lib import load_books_into_session, filter_books
from lib_db import get_conn

gate()

st.title("🔍検索・一覧・削除")

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

all_books = st.session_state.books

if len(all_books) == 0:
    state = "EMPTY_DB"
elif len(books_to_show) == 0:
    state = "EMPTY_FILTER"
else:
    state = "HAS_RESULTS"

df = pd.DataFrame(books_to_show)

if state == "EMPTY_DB":
    st.info("まだ本が登録されていません。Home画面で本を追加してください。")

elif state == "EMPTY_FILTER":
    st.info("検索条件に該当する本がありません。条件を変えてみてください。")

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

if state != "HAS_RESULTS":
    st.caption("削除は表示中の本があるときに利用できます。")
else:
    # 確認待ち情報
    if "pending_delete" not in st.session_state:
        st.session_state.pending_delete = None

    def set_pending(book_id: int, title: str, source: str, label: str):
        st.session_state.pending_delete = {
            "id": book_id,
            "title": title,
            "source": source,  # "no" or "select"
            "label": label,    # 表示用
        }

    def clear_pending():
        st.session_state.pending_delete = None

    pending = st.session_state.pending_delete

    pending = st.session_state.pending_delete

    # 古い形式の pending_delete が残っていたらクリア
    if isinstance(pending, dict) and ("source" not in pending or "label" not in pending):
        st.session_state.pending_delete = None
        pending = None


    if books_to_show:
        # --- No で削除（確認へ） ---
        st.write("### No.で削除（確認へ）")
        no_max = len(books_to_show)
        no_to_delete = st.number_input(
            "削除したい本の『No.』を入力（現在の表示に対応）",
            min_value=1, max_value=no_max, step=1
        )

        confirm_area_no = st.empty()

        if st.button("No.で削除（確認へ）", key="prepare_delete_by_no"):
            idx = int(no_to_delete) - 1
            book = books_to_show[idx]
            set_pending(book_id=book["id"], title=book["title"], source="no", label=f"No.{no_to_delete}")

        pending = st.session_state.pending_delete

        # No側の確認UI（この場所に出す）
        if pending and pending.get("source") == "no":
            with confirm_area_no.container():
                st.warning(f"削除確認：『{pending['title']}』を削除しますか？（{pending['label']}）")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("削除を確定する", key="confirm_delete_no"):
                        with get_conn() as conn:
                            conn.execute("DELETE FROM books WHERE id = ?", (pending["id"],))
                            conn.commit()
                        load_books_into_session(st)
                        st.success(f"『{pending['title']}』を削除しました。")
                        clear_pending()
                with c2:
                    if st.button("キャンセル", key="cancel_delete_no"):
                        st.info("削除をキャンセルしました。")
                        clear_pending()

        st.divider()

        # --- 選択で削除（確認へ） ---
        st.write("### 選択で削除（確認へ）")
        options = [(i + 1, book["id"], book["title"]) for i, book in enumerate(books_to_show)]
        selected = st.selectbox(
            "削除する本を選んでください（現在の表示に対応）",
            options,
            format_func=lambda x: f"No.{x[0]} | {x[2]}",
            key="delete_selectbox"
        )

        confirm_area_sel = st.empty()

        if st.button("選んだ本を削除（確認へ）", key="prepare_delete_by_select"):
            no, book_id, title = selected
            set_pending(book_id=book_id, title=title, source="select", label=f"No.{no}（選択）")

        pending = st.session_state.pending_delete 

        # 選択側の確認UI（この場所に出す）
        if pending and pending.get("source") == "select":
            with confirm_area_sel.container():
                st.warning(f"削除確認：『{pending['title']}』を削除しますか？（{pending['label']}）")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("削除を確定する", key="confirm_delete_select"):
                        with get_conn() as conn:
                            conn.execute("DELETE FROM books WHERE id = ?", (pending["id"],))
                            conn.commit()
                        load_books_into_session(st)
                        st.success(f"『{pending['title']}』を削除しました。")
                        clear_pending()
                with c2:
                    if st.button("キャンセル", key="cancel_delete_select"):
                        st.info("削除をキャンセルしました。")
                        clear_pending()

