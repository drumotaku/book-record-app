# pages/share.py
import streamlit as st
import urllib.parse
from lib import get_conn, resolve_share, fetch_books_by_ids

st.set_page_config(page_title="共有ビュー", page_icon="📚")
st.markdown('<meta name="robots" content="noindex">', unsafe_allow_html=True)
st.title("共有ビュー")

# ?token=... を取得
params = st.experimental_get_query_params()
token = params.get("token", [None])[0]
if not token:
    st.warning("共有トークンが指定されていません。")
    st.stop()

# 共有セットを解決
with get_conn() as conn:
    book_ids, err = resolve_share(conn, token)

if err == "not_found":
    st.error("共有リンクが存在しません。"); st.stop()
if err == "revoked":
    st.error("この共有リンクは失効しています。"); st.stop()
if err == "expired":
    st.error("この共有リンクは期限切れです。"); st.stop()
if not book_ids:
    st.info("共有セットに本がありません。"); st.stop()

# 本情報を取得
with get_conn() as conn:
    books = fetch_books_by_ids(conn, book_ids)

def amazon_search_url(title: str, author: str = "") -> str:
    q = "+".join([s for s in [title, author] if s]).replace(" ", "+")
    return f"https://www.amazon.co.jp/s?k={urllib.parse.quote_plus(q)}"

# 一覧＋Amazonリンク
for b in books:
    st.subheader(b["title"])
    st.write(f'著者: {b.get("author","不明")}')
    if b.get("read_on"): st.caption(f'読了日: {b["read_on"]}')
    if b.get("rating") is not None: st.caption(f'評価: {b["rating"]}')
    aurl = b.get("amazon_url") if b.get("amazon_url") else amazon_search_url(b["title"], b.get("author",""))
    st.link_button("Amazonで見る", aurl)
    st.divider()
