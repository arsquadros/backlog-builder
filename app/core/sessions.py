import streamlit as st

from typing import Dict
from app.static.styles import STYLES_WEBSITE


def init_state():
    defaults = {
        "authenticated": False,
        "backlog": [],
        "sel": {
            "epic": None,
            "feat": None,
            "back": None
        },
        "project_name": "Meu Backlog 001",
        "page": "dashboard",
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
            
            
def apply_styles():
    st.markdown(STYLES_WEBSITE, unsafe_allow_html=True)


def edit_modal(item: Dict, key_prefix: str):
    with st.popover("📝", use_container_width=False):
        new_title = st.text_input("Título", value=item['title'], key=f"t_{key_prefix}")
        new_resp = st.text_input("Responsável", value=item['responsible'], key=f"r_{key_prefix}")
        if st.button("Salvar", key=f"s_{key_prefix}"):
            item['title'] = new_title
            item['responsible'] = new_resp
            st.rerun()


def reset_selection(level: str):
    levels = ["epic", "feat", "back"]
    idx = levels.index(level)
    for l in levels[idx+1:]: st.session_state.sel[l] = None
