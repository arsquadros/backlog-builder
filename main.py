import streamlit as st
import json
from datetime import datetime
from typing import List

# --- 1. CONFIGURAÇÕES E ESTILOS ---
def apply_custom_styles():
    st.markdown("""
        <style>
        /* Estilização dos Cards (Botões disfarçados) */
        .stButton > button {
            border: 1px solid #ddd;
            text-align: left;
            padding: 1rem;
            border-radius: 10px;
            background-color: rgba(255, 255, 255, 0.7);
            transition: all 0.2s ease;
            display: block;
            margin-bottom: 10px;
        }
        
        /* Cores Laterais por Tipo */
        .epic-btn > div [data-testid="stButton"] button { border-left: 8px solid #8e44ad; }
        .feat-btn > div [data-testid="stButton"] button { border-left: 8px solid #27ae60; }
        .back-btn > div [data-testid="stButton"] button { border-left: 8px solid #f39c12; }
        
        /* Destaque de Seleção */
        .selected-item > div [data-testid="stButton"] button {
            background-color: rgba(0, 0, 0, 0.05);
            border-width: 2px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        /* Cards de Tarefa (Estáticos) */
        .task-card {
            padding: 15px;
            border-radius: 10px;
            background-color: rgba(52, 152, 219, 0.2);
            border-left: 8px solid #2980b9;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 2. LÓGICA DE ESTADO ---
def init_state():
    if 'backlog' not in st.session_state:
        st.session_state.backlog = []
    if 'sel' not in st.session_state:
        st.session_state.sel = {"epic": None, "feat": None, "back": None}

def reset_selection(level: str):
    """Limpa seleções inferiores quando um nível superior muda."""
    levels = ["epic", "feat", "back"]
    start_reset = False
    for l in levels:
        if start_reset:
            st.session_state.sel[l] = None
        if l == level:
            start_reset = True

# --- 3. COMPONENTES DE UI ---
def render_adder(label: str, target_list: List, level_key: str):
    with st.popover(f"➕ {label}"):
        title = st.text_input(f"Título do {label}", key=f"in_t_{level_key}")
        resp = st.text_input("Responsável", key=f"in_r_{level_key}")
        if st.button("Salvar", key=f"btn_save_{level_key}"):
            new_item = {
                "id": f"{level_key.upper()}-{datetime.now().strftime('%M%S')}",
                "title": title,
                "responsible": resp,
                "children": []
            }
            target_list.append(new_item)
            st.rerun()

def main():
    st.set_page_config(page_title="Backlog Builder Pro", layout="wide")
    apply_custom_styles()
    init_state()

    st.title("🚀 Backlog Builder")

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Ferramentas")
        
        # Import/Export
        uploaded = st.file_uploader("Importar JSON", type="json")
        if uploaded:
            st.session_state.backlog = json.load(uploaded)
            st.success("Dados carregados!")

        json_str = json.dumps(st.session_state.backlog, indent=2)
        st.download_button("📥 Exportar JSON", data=json_str, file_name="backlog.json")
        
        if st.button("🗑️ Limpar Tudo"):
            st.session_state.backlog = []
            st.session_state.sel = {"epic": None, "feat": None, "back": None}
            st.rerun()

    # --- TABULEIRO PRINCIPAL (4 COLUNAS) ---
    c1, c2, c3, c4 = st.columns(4)

    # COLUNA 1: ÉPICOS
    with c1:
        st.subheader("🟣 Épicos")
        render_adder("Épico", st.session_state.backlog, "epic")
        for ep in st.session_state.backlog:
            is_sel = st.session_state.sel["epic"] == ep["id"]
            css_class = "epic-btn selected-item" if is_sel else "epic-btn"
            with st.container(border=False):
                st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                if st.button(f"**{ep['title']}**\n\n{ep['responsible']}", key=f"ep_{ep['id']}", use_container_width=True):
                    st.session_state.sel["epic"] = ep["id"]
                    reset_selection("epic")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # COLUNA 2: FEATURES
    with c2:
        st.subheader("🟢 Features")
        if st.session_state.sel["epic"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            render_adder("Feature", curr_ep["children"], "feat")
            for ft in curr_ep["children"]:
                is_sel = st.session_state.sel["feat"] == ft["id"]
                css_class = "feat-btn selected-item" if is_sel else "feat-btn"
                with st.container(border=False):
                    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                    if st.button(f"**{ft['title']}**\n\n{ft['responsible']}", key=f"ft_{ft['id']}", use_container_width=True):
                        st.session_state.sel["feat"] = ft["id"]
                        reset_selection("feat")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Selecione um Épico")

    # COLUNA 3: BACKLOG
    with c3:
        st.subheader("🟡 Backlog")
        if st.session_state.sel["feat"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            curr_ft = next(x for x in curr_ep["children"] if x['id'] == st.session_state.sel["feat"])
            render_adder("Backlog", curr_ft["children"], "back")
            for bk in curr_ft["children"]:
                is_sel = st.session_state.sel["back"] == bk["id"]
                css_class = "back-btn selected-item" if is_sel else "back-btn"
                with st.container(border=False):
                    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                    if st.button(f"**{bk['title']}**\n\n{bk['responsible']}", key=f"bk_{bk['id']}", use_container_width=True):
                        st.session_state.sel["back"] = bk["id"]
                        reset_selection("back")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Selecione uma Feature")

    # COLUNA 4: TAREFAS
    with c4:
        st.subheader("🔵 Tarefas")
        if st.session_state.sel["back"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            curr_ft = next(x for x in curr_ep["children"] if x['id'] == st.session_state.sel["feat"])
            curr_bk = next(x for x in curr_ft["children"] if x['id'] == st.session_state.sel["back"])
            render_adder("Tarefa", curr_bk["children"], "task")
            for tk in curr_bk["children"]:
                st.markdown(f'''
                    <div class="task-card">
                        <b>{tk['title']}</b><br>
                        <small>👤 {tk['responsible']}</small>
                    </div>
                ''', unsafe_allow_html=True)
        else:
            st.info("Selecione um item do Backlog")

        # --- EXTRA DETALHES (Visão de 1 coluna) ---
    st.divider()
    st.subheader("📋 Detalhes Completos (Hierarquia Vertical)")
    for ep in st.session_state.backlog:
        with st.expander(f"🟣 ÉPICO: {ep['title']} ({ep['responsible']})"):
            for ft in ep['children']:
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**🟢 Feature:** {ft['title']} | {ft['responsible']}")
                for bk in ft['children']:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**🟡 Backlog:** {bk['title']}")
                    for tk in bk['children']:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**🔵 Tarefa:** {tk['title']} ({tk['responsible']})")


if __name__ == "__main__":
    main()