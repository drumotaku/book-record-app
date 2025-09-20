import streamlit as st
st.set_page_config(page_title="ログイン")
from utils_auth import gate
gate()