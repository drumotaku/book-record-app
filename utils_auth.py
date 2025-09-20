import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

def gate():
    st.set_page_config(page_title="認証")

    if st.session_state.get("authed"):
        return
    
    st.title("認証が必要です")
    try:
        real = st.secrets["APP_PASSWORD"]
    except (KeyError, StreamlitSecretNotFoundError):
        st.warning("管理者向け：SecretsにAPP_PASSWORDを設定してください。")
        st.stop()

    pw = st.text_input("パスワードを入力してください", type="password")
    ok = st.button("認証")

    if not ok:
        st.stop()

    if real and pw == real:
        st.session_state["authed"] = True
        st.rerun()
    else:
        st.error("パスワードが違います")
        st.stop()