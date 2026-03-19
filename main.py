import streamlit as st
import json
from datetime import datetime

# --- 1. CONFIGURAÇÕES E ESTILOS ---
def apply_custom_styles():
    st.markdown("""
        <style>
        .breadcrumb { 
            padding: 10px; border-radius: 5px; background-color: #f0f2f6; 
            margin-bottom: 20px; border-left: 5px solid #ff4b4b; font-family: monospace;
        }
        .stButton > button {
            border: 1px solid #ddd; text-align: left; padding: 1rem; border-radius: 10px;
            background-color: rgba(255, 255, 255, 0.7); transition: all 0.2s ease;
            display: block; margin-bottom: 10px;
        }
        .epic-btn > div [data-testid="stButton"] button { border-left: 8px solid #8e44ad; }
        .feat-btn > div [data-testid="stButton"] button { border-left: 8px solid #27ae60; }
        .back-btn > div [data-testid="stButton"] button { border-left: 8px solid #f39c12; }
        .selected-item > div [data-testid="stButton"] button {
            background-color: rgba(142, 68, 173, 0.1); border-width: 2px; border-color: #8e44ad;
        }
        .task-card {
            padding: 15px; border-radius: 10px; background-color: rgba(52, 152, 219, 0.15);
            border-left: 8px solid #2980b9; margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 2. LOGICA DE LIMPEZA DE DADOS (JSON) ---
def clean_backlog_data(data_list):
    """Remove IDs e metadados de UI para uma exportação limpa."""
    clean_list = []
    for item in data_list:
        clean_item = {
            "titulo": item["title"],
            "responsavel": item["responsible"]
        }
        if item.get("children"):
            clean_item["sub_itens"] = clean_backlog_data(item["children"])
        clean_list.append(clean_item)
    return clean_list

# --- 3. GESTÃO DE NAVEGAÇÃO ---
def get_breadcrumb():
    """Constrói a string de navegação baseada na seleção atual."""
    path = ["🏠 Início"]
    if st.session_state.sel["epic"]:
        ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
        path.append(f"🟣 {ep['title']}")
        if st.session_state.sel["feat"]:
            ft = next(x for x in ep["children"] if x['id'] == st.session_state.sel["feat"])
            path.append(f"🟢 {ft['title']}")
            if st.session_state.sel["back"]:
                bk = next(x for x in ft["children"] if x['id'] == st.session_state.sel["back"])
                path.append(f"🟡 {bk['title']}")
    return " > ".join(path)

# --- 4. FUNÇÕES DE ESTADO ---
def init_state():
    if 'backlog' not in st.session_state: st.session_state.backlog = []
    if 'sel' not in st.session_state: st.session_state.sel = {"epic": None, "feat": None, "back": None}

def reset_selection(level):
    levels = ["epic", "feat", "back"]
    start_reset = False
    for l in levels:
        if start_reset: st.session_state.sel[l] = None
        if l == level: start_reset = True

# --- 5. INTERFACE PRINCIPAL ---
def main():
    st.set_page_config(page_title="Backlog Architect", layout="wide")
    apply_custom_styles()
    init_state()

    st.title("🚀 Backlog Builder")
    
    # Exibe a localização atual (Breadcrumb)
    st.markdown(f'<div class="breadcrumb">{get_breadcrumb()}</div>', unsafe_allow_html=True)

    # SIDEBAR
    with st.sidebar:
        st.header("💾 Dados")
        uploaded = st.file_uploader("Importar JSON", type="json")
        if uploaded:
            st.session_state.backlog = json.load(uploaded)
            st.rerun()

        st.divider()
        # Exportação Limpa
        clean_data = clean_backlog_data(st.session_state.backlog)
        st.download_button(
            label="📥 Exportar JSON Limpo",
            data=json.dumps(clean_data, indent=4, ensure_ascii=False),
            file_name=f"backlog_limpo_{datetime.now().strftime('%d%m')}.json",
            mime="application/json"
        )
        
        if st.button("🗑️ Resetar Sistema"):
            st.session_state.backlog = []
            st.session_state.sel = {"epic": None, "feat": None, "back": None}
            st.rerun()

    # COLUNAS
    c1, c2, c3, c4 = st.columns(4)

    # COLUNA 1: ÉPICOS
    with c1:
        st.subheader("🟣 Épicos")
        with st.popover("➕ Adicionar"):
            t = st.text_input("Nome do Épico", key="epic_n")
            r = st.text_input("Dono", key="epic_o")
            if st.button("Confirmar Épico"):
                st.session_state.backlog.append({"id": f"E-{datetime.now().microsecond}", "title": t, "responsible": r, "children": []})
                st.rerun()
        
        for ep in st.session_state.backlog:
            is_sel = st.session_state.sel["epic"] == ep["id"]
            container_class = "epic-btn selected-item" if is_sel else "epic-btn"
            st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
            if st.button(f"**{ep['title']}**\n\n👤 {ep['responsible']}", key=f"e_{ep['id']}", use_container_width=True):
                st.session_state.sel["epic"] = ep["id"]
                reset_selection("epic")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # COLUNA 2: FEATURES
    with c2:
        st.subheader("🟢 Features")
        if st.session_state.sel["epic"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            with st.popover("➕ Adicionar"):
                t = st.text_input("Nome da Feature", key="feat_n")
                r = st.text_input("Responsável", key="feat_o")
                if st.button("Confirmar Feature"):
                    curr_ep["children"].append({"id": f"F-{datetime.now().microsecond}", "title": t, "responsible": r, "children": []})
                    st.rerun()
            
            for ft in curr_ep["children"]:
                is_sel = st.session_state.sel["feat"] == ft["id"]
                container_class = "feat-btn selected-item" if is_sel else "feat-btn"
                st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
                if st.button(f"**{ft['title']}**\n\n👤 {ft['responsible']}", key=f"f_{ft['id']}", use_container_width=True):
                    st.session_state.sel["feat"] = ft["id"]
                    reset_selection("feat")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # COLUNA 3: BACKLOG (Items)
    with c3:
        st.subheader("🟡 Backlog")
        if st.session_state.sel["feat"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            curr_ft = next(x for x in curr_ep["children"] if x['id'] == st.session_state.sel["feat"])
            with st.popover("➕ Adicionar"):
                t = st.text_input("Item de Backlog", key="back_n")
                r = st.text_input("Responsável", key="back_o")
                if st.button("Confirmar Item"):
                    curr_ft["children"].append({"id": f"B-{datetime.now().microsecond}", "title": t, "responsible": r, "children": []})
                    st.rerun()

            for bk in curr_ft["children"]:
                is_sel = st.session_state.sel["back"] == bk["id"]
                container_class = "back-btn selected-item" if is_sel else "back-btn"
                st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
                if st.button(f"**{bk['title']}**\n\n👤 {bk['responsible']}", key=f"b_{bk['id']}", use_container_width=True):
                    st.session_state.sel["back"] = bk["id"]
                    reset_selection("back")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # COLUNA 4: TAREFAS
    with c4:
        st.subheader("🔵 Tarefas")
        if st.session_state.sel["back"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            curr_ft = next(x for x in curr_ep["children"] if x['id'] == st.session_state.sel["feat"])
            curr_bk = next(x for x in curr_ft["children"] if x['id'] == st.session_state.sel["back"])
            with st.popover("➕ Adicionar"):
                t = st.text_input("Subtarefa", key="task_n")
                r = st.text_input("Executor", key="task_o")
                if st.button("Confirmar Tarefa"):
                    curr_bk["children"].append({"title": t, "responsible": r})
                    st.rerun()

            for tk in curr_bk["children"]:
                st.markdown(f'<div class="task-card"><b>{tk["title"]}</b><br><small>👤 {tk["responsible"]}</small></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()