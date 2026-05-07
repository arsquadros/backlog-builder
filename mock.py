import streamlit as st

import json
import os
import uuid
import bcrypt

from typing import Dict, List, Optional
from datetime import datetime

from google.cloud import firestore

from weasyprint import HTML

# --- 1. CONFIGURAÇÃO FIRESTORE ---
# O Streamlit busca automaticamente as credenciais em .streamlit/secrets.toml
# ou através da variável de ambiente GOOGLE_APPLICATION_CREDENTIALS
try:
    db = firestore.Client()
except Exception:
    st.warning("⚠️ Firestore não configurado. Verifique as credenciais do Google Cloud.")
    db = None

# --- 2. SEGURANÇA E AUTH ---
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# --- 3. SERVIÇOS DE DADOS ---
class DataService:
    @staticmethod
    def save_project(user_id: str, project_name: str, data: List[Dict]):
        if db:
            doc_ref = db.collection("users").document(user_id).collection("backlogs").document(project_name)
            doc_ref.set({
                "name": project_name,
                "data": data,
                "updated_at": datetime.now()
            })
            return True
        return False

    @staticmethod
    def get_projects(user_id: str):
        if db:
            docs = db.collection("users").document(user_id).collection("backlogs").stream()
            return {doc.id: doc.to_dict() for doc in docs}
        return {}

# --- 4. COMPONENTES DE UI ---
def apply_styles():
    st.markdown("""
        <style>
        .stButton > button { width: 100%; border-radius: 5px; }
        .task-card { 
            padding: 10px; border-radius: 5px; background-color: #f0f2f6; 
            border-left: 5px solid #2980b9; margin-bottom: 5px;
        }
        .selected-column { border: 2px solid #8e44ad; border-radius: 10px; padding: 5px; }
        </style>
    """, unsafe_allow_html=True)

def edit_modal(item: Dict, key_prefix: str):
    with st.popover("📝", use_container_width=False):
        new_title = st.text_input("Título", value=item['title'], key=f"t_{key_prefix}")
        new_resp = st.text_input("Dono", value=item['responsible'], key=f"r_{key_prefix}")
        if st.button("Salvar", key=f"s_{key_prefix}"):
            item['title'] = new_title
            item['responsible'] = new_resp
            st.rerun()

# --- 5. LÓGICA DE NAVEGAÇÃO ---
def init_state():
    if 'backlog' not in st.session_state: st.session_state.backlog = []
    if 'sel' not in st.session_state: st.session_state.sel = {"epic": None, "feat": None, "back": None}
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False

def reset_selection(level: str):
    levels = ["epic", "feat", "back"]
    idx = levels.index(level)
    for l in levels[idx+1:]: st.session_state.sel[l] = None

# --- 6. INTERFACE PRINCIPAL ---
def main():
    st.set_page_config(page_title="Architect Pro", layout="wide")
    apply_styles()
    init_state()

    if not st.session_state.authenticated:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.title("🔐 Login")
            user = st.text_input("Usuário")
            pw = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                # Em um sistema real, você buscaria o hash do usuário no Firestore
                # Aqui usamos um exemplo fixo para demonstração
                mock_hash = hash_password("solides123") 
                if user == "admin" and check_password(pw, mock_hash):
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Credenciais inválidas")
        return

    # SIDEBAR
    with st.sidebar:
        st.title(f"🚀 {st.session_state.user}")
        if st.button("Log out"):
            st.session_state.authenticated = False
            st.rerun()
        
        st.divider()
        st.subheader("📁 Persistência")
        proj_name = st.text_input("Nome do Projeto", value="Meu_Backlog_IA")
        
        if st.button("💾 Salvar no Firestore"):
            if DataService.save_project(st.session_state.user, proj_name, st.session_state.backlog):
                st.success("Salvo!")
        
        st.divider()
        repo = DataService.get_projects(st.session_state.user)
        if repo:
            selected_load = st.selectbox("Carregar Projeto", options=list(repo.keys()))
            if st.button("📂 Abrir"):
                st.session_state.backlog = repo[selected_load]['data']
                st.rerun()

    # DASHBOARD DE EDIÇÃO
    cols = st.columns(4)

    # 1. ÉPICOS
    with cols[0]:
        st.subheader("🟣 Épicos")
        if st.button("➕ Novo Épico"):
            st.session_state.backlog.append({"id": str(uuid.uuid4()), "title": "Novo Épico", "responsible": "Admin", "children": []})
            st.rerun()

        for i, ep in enumerate(st.session_state.backlog):
            is_sel = st.session_state.sel["epic"] == ep["id"]
            with st.container(border=is_sel):
                c_t, c_e, c_d = st.columns([0.6, 0.2, 0.2])
                if c_t.button(ep['title'], key=f"e_b_{ep['id']}"):
                    st.session_state.sel["epic"] = ep["id"]
                    reset_selection("epic")
                    st.rerun()
                with c_e: edit_modal(ep, f"ed_e_{ep['id']}")
                if c_d.button("🗑️", key=f"del_e_{ep['id']}"):
                    st.session_state.backlog.pop(i)
                    st.rerun()

    # 2. FEATURES
    with cols[1]:
        st.subheader("🟢 Features")
        if st.session_state.sel["epic"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            if st.button("➕ Nova Feature"):
                curr_ep["children"].append({"id": str(uuid.uuid4()), "title": "Nova Feature", "responsible": "Dev", "children": []})
                st.rerun()
            
            for i, ft in enumerate(curr_ep["children"]):
                is_sel = st.session_state.sel["feat"] == ft["id"]
                with st.container(border=is_sel):
                    c_t, c_e, c_d = st.columns([0.6, 0.2, 0.2])
                    if c_t.button(ft['title'], key=f"f_b_{ft['id']}"):
                        st.session_state.sel["feat"] = ft["id"]
                        reset_selection("feat")
                        st.rerun()
                    with c_e: edit_modal(ft, f"ed_f_{ft['id']}")
                    if c_d.button("🗑️", key=f"del_f_{ft['id']}"):
                        curr_ep["children"].pop(i)
                        st.rerun()

    # 3. BACKLOG
    with cols[2]:
        st.subheader("🟡 Backlog")
        if st.session_state.sel["feat"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            curr_ft = next(x for x in curr_ep["children"] if x['id'] == st.session_state.sel["feat"])
            if st.button("➕ Novo Item"):
                curr_ft["children"].append({"id": str(uuid.uuid4()), "title": "Novo Item", "responsible": "PO", "children": []})
                st.rerun()

            for i, bk in enumerate(curr_ft["children"]):
                is_sel = st.session_state.sel["back"] == bk["id"]
                with st.container(border=is_sel):
                    c_t, c_e, c_d = st.columns([0.6, 0.2, 0.2])
                    if c_t.button(bk['title'], key=f"b_b_{bk['id']}"):
                        st.session_state.sel["back"] = bk["id"]
                        st.rerun()
                    with c_e: edit_modal(bk, f"ed_b_{bk['id']}")
                    if c_d.button("🗑️", key=f"del_b_{bk['id']}"):
                        curr_ft["children"].pop(i)
                        st.rerun()

    # 4. TAREFAS
    with cols[3]:
        st.subheader("🔵 Tarefas")
        if st.session_state.sel["back"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            curr_ft = next(x for x in curr_ep["children"] if x['id'] == st.session_state.sel["feat"])
            curr_bk = next(x for x in curr_ft["children"] if x['id'] == st.session_state.sel["back"])
            
            with st.popover("➕ Nova Tarefa", use_container_width=True):
                t = st.text_input("Tarefa")
                r = st.text_input("Executor")
                if st.button("Adicionar"):
                    curr_bk["children"].append({"title": t, "responsible": r})
                    st.rerun()

            for i, tk in enumerate(curr_bk["children"]):
                st.markdown(f"""<div class="task-card"><b>{tk['title']}</b><br><small>👤 {tk['responsible']}</small></div>""", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_t_{i}"):
                    curr_bk["children"].pop(i)
                    st.rerun()

if __name__ == "__main__":
    main()