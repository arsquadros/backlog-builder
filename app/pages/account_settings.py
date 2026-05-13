import streamlit as st
from app.service.auth import AuthService
from app.service.db import DataService
from app.service.mail import EmailService

from app.service.validators import (
    is_valid_password,
    is_valid_email
)


def render_account_settings():
    st.title("Configurações de Conta")
    user_id = st.session_state.user_id
    user_info = DataService.get_user_data(user_id)

    if st.button("Voltar"):
        st.session_state.page = "dashboard"
        st.rerun()

    # --- SEÇÃO: ALTERAR SENHA ---
    st.subheader("Segurança")
    with st.expander("Alterar Senha"):
        pw1 = st.text_input("Nova Senha", type="password", key="new_pw1")
        pw2 = st.text_input("Confirme a Nova Senha", type="password", key="new_pw2")
        
        if st.button("Atualizar Senha"):
            ok_v, msg_v = is_valid_password(pw1)
            if not ok_v:
                st.error(msg_v)
            elif pw1 != pw2:
                st.error("As senhas não coincidem.")
            else:
                hashed_pw = AuthService.hash_password(pw1)
                if DataService.update_user_data(user_id, {"password": hashed_pw}):
                    st.success("Senha alterada com sucesso!")
                    EmailService.send_password_change_confirmation(user_info)

    # --- SEÇÃO: ALTERAR E-MAIL ---
    st.subheader("Dados Pessoais")
    st.write(f"E-mail atual: **{user_info.get('email')}**")
    
    if "email_step" not in st.session_state: st.session_state.email_step = "input"

    if st.session_state.email_step == "input":
        new_email = st.text_input("Novo E-mail", key="change_email_val")
        if st.button("Solicitar Troca de E-mail"):
            v_e, m_e = is_valid_email(new_email)
            if not v_e:
                st.error(m_e)
            else:
                code = AuthService.request_email_update(user_id, new_email)
                data = user_info.copy()
                data["email"] = new_email
                EmailService.send_verification_code(data, code, "alterar e-mail")
                st.session_state.email_step = "verify"
                st.session_state.new_email = new_email
                st.rerun()

    elif st.session_state.email_step == "verify":
        code_in = st.text_input("Digite o código enviado ao novo e-mail")
        col1, col2 = st.columns(2)
        if col1.button("Confirmar Alteração"):
            ok, msg = AuthService.confirm_email_update(user_id, code_in)
            if ok:
                st.success(msg)
                st.session_state.email_step = "input"
                data = user_info.copy()
                data["email"] = st.session_state.new_email
                EmailService.send_welcome_email(data)
                st.rerun()
            else:
                st.error(msg)
        if col2.button("Cancelar"):
            st.session_state.email_step = "input"
            st.rerun()

    st.divider()
    
    st.subheader("Zona de Perigo")
    st.warning("A exclusão da conta é permanente e removerá todos os seus backlogs.")
    confirm = st.checkbox("Estou ciente de que todos os meus dados serão apagados.")
    
    if st.button("Excluir Minha Conta", type="primary", disabled=not confirm):

        if AuthService.delete_account(user_id):
            EmailService.send_account_deletion_confirmation(user_info)
            st.session_state.authenticated = False
            st.rerun()
        else:
            st.error("Erro ao excluir conta.")
