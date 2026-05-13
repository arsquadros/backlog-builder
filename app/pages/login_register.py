import streamlit as st
from app.core.sessions import apply_styles
from app.service.auth import AuthService
from app.service.db import DataService
from app.service.mail import EmailService
from app.service.validators import (
    is_valid_username,
    is_valid_password,
    is_valid_email
)

def render_login_register():
    apply_styles()
    tab1, tab2 = st.tabs(["Login", "Cadastro"])

    with tab1:
        user = st.text_input("Usuário", key="login_user")
        pw = st.text_input("Senha", type="password", key="login_pw")
        if st.button("Entrar"):
            if AuthService.authenticate(user, pw):
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.user_id = DataService.get_user_uuid(user)
                st.rerun()
            else:
                st.error("Credenciais inválidas.")

    with tab2:
        # Fluxo de Verificação
        if "reg_step" not in st.session_state: st.session_state.reg_step = "form"
        
        if st.session_state.reg_step == "form":
            new_name = st.text_input("Nome Completo", key="reg_name")
            new_user = st.text_input("Nome de Usuário", key="reg_user")
            new_email = st.text_input("E-mail", key="reg_email")
            new_pw1 = st.text_input("Senha", type="password", key="reg_pw1")
            new_pw2 = st.text_input("Repita a Senha", type="password", key="reg_pw2")

            if st.button("Solicitar Cadastro"):
                # Validações sequenciais
                v_u, m_u = is_valid_username(new_user)
                v_p, m_p = is_valid_password(new_pw1)
                v_e, m_e = is_valid_email(new_email)
                
                if not v_u: st.error(m_u)
                elif not v_e: st.error(m_e)
                elif not v_p: st.error(m_p)
                elif new_pw1 != new_pw2: st.error("Senhas não coincidem")
                else:
                    success, code_or_msg = AuthService.request_registration(new_user, new_pw1, new_name, new_email)
                    if success:
                        data = {"name": new_name, "username": new_user, "email": new_email}
                        EmailService.send_verification_code(data, code_or_msg)
                        st.session_state.temp_user = new_user
                        st.session_state.reg_step = "verify"
                        st.rerun()
                    else:
                        st.error(code_or_msg)

        elif st.session_state.reg_step == "verify":
            st.info(f"Insira o código enviado para o seu e-mail.")
            code_in = st.text_input("Código de Verificação", key="verify_code")
            if st.button("Confirmar Conta"):
                ok, msg = AuthService.confirm_registration(st.session_state.temp_user, code_in)
                if ok:
                    st.success(msg)
                    EmailService.send_welcome_email(DataService.get_user_data(DataService.get_user_uuid(st.session_state.temp_user)))
                    st.session_state.reg_step = "form"
                else:
                    st.error(msg)
            if st.button("Voltar"):
                st.session_state.reg_step = "form"
                st.rerun()