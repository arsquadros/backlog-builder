import streamlit as st

from app.core.sessions import edit_modal
from app.core.sessions import reset_selection
from app.core.sessions import apply_styles

from app.service.db import DataService
from app.service.doc import DocService
from app.service.mail import EmailService
from app.service.ai import AIService

import uuid


def render_dashboard():
    apply_styles()
    
    st.title("Architect Pro")

    with st.sidebar:
        st.subheader(f"Olá, {st.session_state.user}!")

        col_config, col_logout = st.columns([0.6, 0.4])

        if col_config.button("Configurações de Conta"):
            st.session_state.page = "settings"
            st.rerun()

        if col_logout.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

        st.divider()
        st.subheader("Projetos")

        col_project_name, col_project_name_save = st.columns([0.6, 0.3])
        
        project = col_project_name.text_input(
            "Nome do Projeto em Edição",
            value=st.session_state.project_name
        )

        if col_project_name_save.button("Salvar"):
            saved = DataService.save_project(
                st.session_state.user,
                project,
                st.session_state.backlog
            )
            if saved:
                st.success(f"O Projeto \"{project}\" foi salvo com sucesso.")
            else:
                st.error(f"Não foi possível salvar o projeto \"{project}\". Tente novamente em alguns instantes.")

        repo = DataService.get_projects(st.session_state.user)
        if repo:
            col_sel, col_del = st.columns([0.8, 0.2])
            selected_load = col_sel.selectbox("Carregar Projeto", options=list(repo.keys()))
            if col_sel.button("Carregar"):
                st.session_state.backlog = repo[selected_load]['data']
                st.session_state.project_name = selected_load
                st.rerun()
            if col_del.button("🗑️", help="Deletar Projeto Selecionado"):
                if DataService.delete_project(st.session_state.user, selected_load):
                    st.success("Projeto removido")
                    st.rerun()

        st.divider()
        st.subheader("Relatórios")
    
        col_basic_report, col_ai_report = st.columns([0.4, 0.6])

        if col_basic_report.button("Gerar PDF"):
            with st.spinner("Estamos construindo o seu relatório em PDF..."):
                doc_pdf = DataService.generate_pdf(project, st.session_state.backlog)
                sucesso = EmailService.send_basic_backlog_report(DataService.get_user_data(st.session_state.user_id), project, doc_pdf)

                if sucesso:
                    st.success(f"Enviamos o documento para o seu e-mail cadastrado.")
        if col_ai_report.button("Gerar Documentação (IA)"):
            can_gen, msg_ai = AIService.can_generate_ai_report(st.session_state.user_id)
            if not can_gen:
                st.warning(msg_ai)
            else:
                with st.spinner("Estamos construindo o seu relatório de IA..."):
                    doc_pdf = DocService.generate_doc_report(project, st.session_state.backlog)
                    sucesso = EmailService.send_ai_backlog_report(DataService.get_user_data(st.session_state.user_id), project, doc_pdf)

                    if sucesso:
                        st.success(f"Enviamos o documento para o seu e-mail cadastrado.")

                    #st.download_button(
                    #    label="Baixar Relatório de PBIs",
                    #    data=doc_pdf,
                    #    file_name=f"DOC_{project}.pdf",
                    #    mime="application/pdf"
                    #)

    cols = st.columns(4)

    with cols[0]:
        st.subheader("🟣 Épicos")
        if st.button("Novo Épico"):
            st.session_state.backlog.append({"id": str(uuid.uuid4()), "title": "Novo Épico", "responsible": st.session_state.user, "children": []})
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
                st.markdown(f"<div class='card-info'>👤 {ep['responsible']}</div>", unsafe_allow_html=True)

    with cols[1]:
        st.subheader("🟢 Features")
        if st.session_state.sel["epic"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            if st.button("Nova Feature"):
                curr_ep["children"].append({"id": str(uuid.uuid4()), "title": "Nova Feature", "responsible": "Time Dev", "children": []})
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
                    st.markdown(f"<div class='card-info'>👤 {ft['responsible']}</div>", unsafe_allow_html=True)

    with cols[2]:
        st.subheader("🟡 Itens")
        if st.session_state.sel["feat"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            curr_ft = next(x for x in curr_ep["children"] if x['id'] == st.session_state.sel["feat"])
            if st.button("Novo Item"):
                curr_ft["children"].append({"id": str(uuid.uuid4()), "title": "Requisito X", "responsible": "PO", "children": []})
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
                    st.markdown(f"<div class='card-info'>👤 {bk['responsible']}</div>", unsafe_allow_html=True)

    with cols[3]:
        st.subheader("🔵 Tarefas")
        if st.session_state.sel["back"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            curr_ft = next(x for x in curr_ep["children"] if x['id'] == st.session_state.sel["feat"])
            curr_bk = next(x for x in curr_ft["children"] if x['id'] == st.session_state.sel["back"])
            
            with st.popover("Adicionar Tarefa", use_container_width=True):
                t = st.text_input("O que fazer?")
                r = st.text_input("Quem?")
                if st.button("Adicionar"):
                    curr_bk["children"].append({"title": t, "responsible": r})
                    st.rerun()

            for i, tk in enumerate(curr_bk["children"]):
                with st.container():
                    col_card, col_delete_card = st.columns([0.8, 0.2])
                    col_card.markdown(f"""
                        <div class="task-card">
                            <b>{tk['title']}</b><br>
                            <small>👤 {tk['responsible']}</small>
                        </div>
                    """, unsafe_allow_html=True)
                    if col_delete_card.button("🗑️", key=f"del_t_{i}"):
                        curr_bk["children"].pop(i)
                        
                        st.rerun()
