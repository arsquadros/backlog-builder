import streamlit as st
import json
from datetime import datetime
from weasyprint import HTML

# --- 1. CONFIGURAÇÕES E ESTILOS UI ---
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
            display: block; margin-bottom: 10px; width: 100%;
        }
        .del-btn > div [data-testid="stButton"] button {
            background-color: transparent; border: none; color: #ff4b4b; padding: 0.5rem; text-align: center;
        }
        .epic-btn > div [data-testid="stButton"] button { border-left: 8px solid #8e44ad; }
        .feat-btn > div [data-testid="stButton"] button { border-left: 8px solid #27ae60; }
        .back-btn > div [data-testid="stButton"] button { border-left: 8px solid #f39c12; }
        .selected-item > div [data-testid="stButton"] button {
            background-color: rgba(142, 68, 173, 0.1); border-width: 2px; border-color: #8e44ad;
        }
        .task-card {
            padding: 15px; border-radius: 10px; background-color: rgba(52, 152, 219, 0.15);
            border-left: 8px solid #2980b9; margin-bottom: 10px; position: relative;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 2. LOGICA DE EXPORTAÇÃO PDF ---
def generate_pdf_weasy(backlog_data):
    def build_html_tree(items, level=0):
        if not items: return ""
        html = "<ul>"
        classes = ["epic", "feat", "back", "task"]
        cls = classes[min(level, 3)]
        for item in items:
            html += f"""<li class="item-{cls}"><div class="content">
                        <span class="title"><strong>{item['title']}</strong></span>
                        <span class="resp">👤 {item['responsible']}</span></div>"""
            if "children" in item and item["children"]:
                html += build_html_tree(item["children"], level + 1)
            html += "</li>"
        return html + "</ul>"

    content_html = build_html_tree(backlog_data)
    full_html = f"""
    <html><head><style>
        @page {{ margin: 2cm; }}
        body {{ font-family: 'Helvetica', sans-serif; color: #333; }}
        h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; }}
        .date {{ text-align: center; font-size: 0.8rem; color: #7f8c8d; margin-bottom: 30px; }}
        ul {{ list-style: none; padding-left: 20px; }}
        li {{ margin-bottom: 8px; padding: 8px; border-radius: 5px; }}
        .item-epic {{ border-left: 5px solid #8e44ad; background: #f8f4fb; margin-top: 15px; }}
        .item-feat {{ border-left: 5px solid #27ae60; background: #f4faf6; }}
        .item-back {{ border-left: 5px solid #f39c12; background: #fefaf2; }}
        .item-task {{ border-left: 5px solid #2980b9; background: #f2f7fb; font-size: 0.9rem; }}
        .content {{ display: flex; justify-content: space-between; }}
        .resp {{ font-style: italic; font-size: 0.85rem; }}
    </style></head>
    <body><h1>Relatório de Backlog</h1><div class="date">Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
    {content_html}</body></html>"""
    return HTML(string=full_html).write_pdf()

# --- 3. GESTÃO DE ESTADO E NAVEGAÇÃO ---
def init_state():
    if 'backlog' not in st.session_state: st.session_state.backlog = []
    if 'sel' not in st.session_state: st.session_state.sel = {"epic": None, "feat": None, "back": None}

def reset_selection(level):
    levels = ["epic", "feat", "back"]
    idx = levels.index(level)
    for l in levels[idx+1:]: st.session_state.sel[l] = None

def get_breadcrumb():
    path = ["🏠 Início"]
    if st.session_state.sel["epic"]:
        ep = next((x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"]), None)
        if ep:
            path.append(f"🟣 {ep['title']}")
            if st.session_state.sel["feat"]:
                ft = next((x for x in ep["children"] if x['id'] == st.session_state.sel["feat"]), None)
                if ft:
                    path.append(f"🟢 {ft['title']}")
                    if st.session_state.sel["back"]:
                        bk = next((x for x in ft["children"] if x['id'] == st.session_state.sel["back"]), None)
                        if bk: path.append(f"🟡 {bk['title']}")
    return " > ".join(path)

# --- 4. LISTA ESTÁTICA DE ÉPICOS ---
SUGGESTED_EPICS = [
    {"title": "Agente RH Gestor", "resp": "IA Team"},
    {"title": "Agente Solidiano", "resp": "IA Team"},
    {"title": "Copy CRM Gen AI", "resp": "IA Team"},
    {"title": "Extrator de Atestado Médico", "resp": "IA Team"},
    {"title": "Fit Scoring", "resp": "IA Team"},
    {"title": "Health Score", "resp": "IA Team"},
    {"title": "Home Unificada", "resp": "IA Team"},
    {"title": "Jobs Recommender", "resp": "IA Team"},
    {"title": "Next Best Offer", "resp": "IA Team"},
    {"title": "Produção Científica", "resp": "IA Team"},
    {"title": "Recolocação Profissional", "resp": "IA Team"},
    {"title": "Recomendador de Candidatos", "resp": "IA Team"},
    {"title": "Soliris", "resp": "IA Team"},
    {"title": "Turnover (Evolução)", "resp": "IA Team"},
    {"title": "Video Profiler", "resp": "IA Team"},

    {"title": "Dashboard Projetos", "resp": "IA Team"},
    {"title": "Recorrências", "resp": "IA Team"},
    {"title": "Agent Starter", "resp": "IA Team"},
    {"title": "Agent Platform", "resp": "IA Team"},
    {"title": "Smart Onboarding", "resp": "IA Team"},
    {"title": "Holerite", "resp": "IA Team"},
    {"title": "Migração de Sistemas", "resp": "IA Team"},
    {"title": "Atividades Operacionais", "resp": "IA Team"},
    {"title": "Eng. Dados", "resp": "IA Team"},
    {"title": "Automação de Extração de Informação Web", "resp": "IA Team"},
    {"title": "Iniciativas de IA GCP + Sólides", "resp": "IA Team"},
    {"title": "MLOps", "resp": "IA Team"},
    {"title": "Fluxo de Automação Comercial", "resp": "IA Team"},
    {"title": "RPA eSocial", "resp": "IA Team"},
    {"title": "Manutenção", "resp": "IA Team"},
]

# --- 5. INTERFACE PRINCIPAL ---
def main():
    st.set_page_config(page_title="Backlog Architect", layout="wide")
    apply_custom_styles()
    init_state()

    st.title("🚀 Backlog Builder")
    st.markdown(f'<div class="breadcrumb">{get_breadcrumb()}</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("💾 Gestão")
        uploaded = st.file_uploader("Importar JSON", type="json")
        if uploaded:
            st.session_state.backlog = json.load(uploaded)
            st.rerun()

        if st.session_state.backlog:
            try:
                pdf_bytes = generate_pdf_weasy(st.session_state.backlog)
                st.download_button("📄 Baixar PDF Profissional", pdf_bytes, f"backlog_{datetime.now().strftime('%d%m')}.pdf", "application/pdf", use_container_width=True)
            except Exception as e: st.error(f"Erro PDF: {e}")
        
        if st.button("🗑️ Limpar Tudo", use_container_width=True):
            st.session_state.backlog = []
            st.session_state.sel = {"epic": None, "feat": None, "back": None}
            st.rerun()

        st.divider()
        st.subheader("💡 Sugestões de Épicos")
        for sug in SUGGESTED_EPICS:
            if st.button(f"➕ {sug['title']}", key=f"sug_{sug['title']}", use_container_width=True):
                st.session_state.backlog.append({
                    "id": f"E-{datetime.now().microsecond}", 
                    "title": sug['title'], 
                    "responsible": sug['resp'], 
                    "children": []
                })
                st.rerun()

    # LAYOUT DE COLUNAS
    c1, c2, c3, c4 = st.columns(4)

    # COLUNA 1: ÉPICOS
    with c1:
        st.subheader("🟣 Épicos")
        with st.popover("➕ Novo Épico"):
            t = st.text_input("Nome", key="e_n")
            r = st.text_input("Dono", key="e_o")
            if st.button("Salvar Épico"):
                st.session_state.backlog.append({"id": f"E-{datetime.now().microsecond}", "title": t, "responsible": r, "children": []})
                st.rerun()
        
        for i, ep in enumerate(st.session_state.backlog):
            col_sel, col_del = st.columns([0.8, 0.2])
            is_sel = st.session_state.sel["epic"] == ep["id"]
            with col_sel:
                container = "epic-btn selected-item" if is_sel else "epic-btn"
                st.markdown(f'<div class="{container}">', unsafe_allow_html=True)
                if st.button(f"{ep['title']}", key=f"btn_{ep['id']}", use_container_width=True):
                    st.session_state.sel["epic"] = ep["id"]
                    reset_selection("epic")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with col_del:
                st.markdown('<div class="del-btn">', unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_e_{ep['id']}"):
                    st.session_state.backlog.pop(i)
                    if is_sel: st.session_state.sel["epic"] = None
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # COLUNA 2: FEATURES
    with c2:
        st.subheader("🟢 Features")
        if st.session_state.sel["epic"] and st.session_state.backlog != []:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            with st.popover("➕ Nova Feature"):
                t = st.text_input("Nome", key="f_n")
                r = st.text_input("Resp", key="f_o")
                if st.button("Salvar Feature"):
                    curr_ep["children"].append({"id": f"F-{datetime.now().microsecond}", "title": t, "responsible": r, "children": []})
                    st.rerun()
            
            for i, ft in enumerate(curr_ep["children"]):
                col_sel, col_del = st.columns([0.8, 0.2])
                is_sel = st.session_state.sel["feat"] == ft["id"]
                with col_sel:
                    container = "feat-btn selected-item" if is_sel else "feat-btn"
                    st.markdown(f'<div class="{container}">', unsafe_allow_html=True)
                    if st.button(f"{ft['title']}", key=f"btn_{ft['id']}"):
                        st.session_state.sel["feat"] = ft["id"]
                        reset_selection("feat")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with col_del:
                    st.markdown('<div class="del-btn">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_f_{ft['id']}"):
                        curr_ep["children"].pop(i)
                        if is_sel: st.session_state.sel["feat"] = None
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # COLUNA 3: BACKLOG (Items)
    with c3:
        st.subheader("🟡 Backlog")
        if st.session_state.sel["feat"] and st.session_state.backlog != []:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            curr_ft = next(x for x in curr_ep["children"] if x['id'] == st.session_state.sel["feat"])
            with st.popover("➕ Novo Item"):
                t = st.text_input("Item", key="b_n")
                r = st.text_input("Resp", key="b_o")
                if st.button("Salvar Item"):
                    curr_ft["children"].append({"id": f"B-{datetime.now().microsecond}", "title": t, "responsible": r, "children": []})
                    st.rerun()

            for i, bk in enumerate(curr_ft["children"]):
                col_sel, col_del = st.columns([0.8, 0.2])
                is_sel = st.session_state.sel["back"] == bk["id"]
                with col_sel:
                    container = "back-btn selected-item" if is_sel else "back-btn"
                    st.markdown(f'<div class="{container}">', unsafe_allow_html=True)
                    if st.button(f"{bk['title']}", key=f"btn_{bk['id']}"):
                        st.session_state.sel["back"] = bk["id"]
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with col_del:
                    st.markdown('<div class="del-btn">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_b_{bk['id']}"):
                        curr_ft["children"].pop(i)
                        if is_sel: st.session_state.sel["back"] = None
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # COLUNA 4: TAREFAS
    with c4:
        st.subheader("🔵 Tarefas")
        if st.session_state.sel["back"] and st.session_state.backlog != []:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            curr_ft = next(x for x in curr_ep["children"] if x['id'] == st.session_state.sel["feat"])
            curr_bk = next(x for x in curr_ft["children"] if x['id'] == st.session_state.sel["back"])
            with st.popover("➕ Nova Tarefa"):
                t = st.text_input("Tarefa", key="t_n")
                r = st.text_input("Executor", key="t_o")
                if st.button("Salvar Tarefa"):
                    curr_bk["children"].append({"title": t, "responsible": r})
                    st.rerun()

            for i, tk in enumerate(curr_bk["children"]):
                col_t, col_d = st.columns([0.8, 0.2])
                with col_t:
                    st.markdown(f'<div class="task-card"><b>{tk["title"]}</b><br><small>👤 {tk["responsible"]}</small></div>', unsafe_allow_html=True)
                with col_d:
                    if st.button("🗑️", key=f"del_t_{i}_{tk['title']}"):
                        curr_bk["children"].pop(i)
                        st.rerun()


if __name__ == "__main__":
    main()