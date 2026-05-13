import streamlit as st

from app.core.sessions import init_state, apply_styles

from app.pages.login_register import render_login_register
from app.pages.dashboard import render_dashboard
from app.pages.account_settings import render_account_settings


st.set_page_config(page_title="Architect Pro", layout="wide")

apply_styles()
init_state()


if not st.session_state.authenticated:
    render_login_register()
else:
    if st.session_state.get("page") == "settings":
        render_account_settings()
    else:
        render_dashboard()