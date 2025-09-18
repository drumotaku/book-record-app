import os
import urllib.parse as up
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

def get_base_url() -> str:
    base_default = os.getenv("APP_BASE_URL") or "http://localhost:8501"
    try:
        base = st.secrets.get("APP_BASE_URL", base_default)
    except StreamlitSecretNotFoundError:
        base = base_default
    return base.rstrip("/")

def build_share_url(token: str, key: str = "share") -> str:
    return f"{get_base_url()}/?{key}={up.quote(token)}"
