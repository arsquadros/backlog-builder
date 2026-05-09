import streamlit as st

import uuid
import bcrypt

from typing import Dict, List
from datetime import datetime
from weasyprint import HTML

from google.cloud import firestore
from google.oauth2 import service_account
from google import genai
from google.genai import types


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

class EmailService:
    @staticmethod
    def send_backlog_report(to_email, project_name, username, pdf_data):
        # Configurações (Devem estar no st.secrets)
        smtp_server = st.secrets["smtp_server"]
        smtp_port = st.secrets["smtp_port"]
        sender_email = st.secrets["sender_email"]
        sender_password = st.secrets["sender_password"]

        msg = MIMEMultipart()
        msg['From'] = f"Backlog Builder SMTP <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = f"Documentação do Projeto: {project_name}"

        body = open("documents/email_body.md", "r").read().format(username=username, project_name=project_name)
        msg.attach(MIMEText(body, 'plain'))

        # Anexando o PDF
        part = MIMEApplication(pdf_data, Name=f"{project_name}.pdf")
        part['Content-Disposition'] = f'attachment; filename="{project_name}.pdf"'
        msg.attach(part)

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            st.error(f"Erro ao enviar e-mail: {e}")
            return False


class AIService:
    @staticmethod
    def generate_pbi_description(epic_title, feat_title, item_title, tasks):
        try:
            client = genai.Client(api_key=st.secrets["google_api_key"])
            task_list = ", ".join([t['title'] for t in tasks])
            
            prompt = open("documents/pbi_description.md", "r").read().format(
                epic_title=epic_title,
                feat_title=feat_title,
                item_title=item_title,
                task_list=task_list
            )

            response = client.models.generate_content(
                model=st.secrets["google_model_name"],
                contents=types.Part.from_text(text=prompt),
                config=types.GenerateContentConfig(
                    temperature=0.5
                ),
            )
            client.close()
            return response.text
        except Exception as e:
            return f"Erro ao gerar descrição via IA. Verifique a chave de API. {e}"


class DocService:
    @staticmethod
    def generate_doc_report(project_name, data):
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #2c3e50; }}
                    .pbi-card {{ border: 1px solid #ddd; padding: 20px; margin-bottom: 30px; page-break-inside: avoid; }}
                    .pbi-header {{ background: #2980b9; color: white; padding: 10px; margin: -20px -20px 20px -20px; }}
                    .context-box {{ background: #f9f9f9; padding: 10px; border-left: 5px solid #2980b9; }}
                    .tasks {{ font-size: 0.85em; color: #7f8c8d; margin-top: 10px; }}
                </style>
            </head>
            <body>
                <h1>Documentação de Requisitos: {project_name}</h1>
        """
        
        for ep in data:
            for ft in ep.get('children', []):
                for bk in ft.get('children', []):
                    desc = AIService.generate_pbi_description(ep['title'], ft['title'], bk['title'], bk.get('children', []))
                    html_content += f"""
                    <div class='pbi-card'>
                        <div class='pbi-header'><strong>ITEM: {bk['title']}</strong> (Ref: {ft['title']})</div>
                        <div class='context-box'>{desc.replace(chr(10), '<br>')}</div>
                        <div class='tasks'><strong>Tarefas relacionadas:</strong> {", ".join([t['title'] for t in bk.get('children', [])])}</div>
                    </div>
                    """
        
        html_content += "</body></html>"
        return HTML(string=html_content).write_pdf()


# --- 1. CONFIGURAÇÃO FIRESTORE ---
def get_firestore_client():
    try:
        # Se estivermos no Streamlit Cloud (ou local com secrets.toml)
        if "gcp_service_account" in st.secrets:
            # Transforma o objeto de secrets em um dicionário comum
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = service_account.Credentials.from_service_account_info(creds_dict)
            return firestore.Client(credentials=creds, project=creds_dict.get("project_id"))
        
        # Fallback para ambiente local que já tenha o gcloud configurado
        return firestore.Client()
    except Exception as e:
        st.error(f"Erro ao configurar Firestore: {e}")
        return None

db = get_firestore_client()

# --- 2. SEGURANÇA E SERVIÇOS DE AUTH ---
class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def check_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @staticmethod
    def create_user(username: str, password: str):
        if not db: return False
        user_ref = db.collection("users").document(username)
        if user_ref.get().exists:
            return False
        user_ref.set({
            "username": username,
            "password": AuthService.hash_password(password),
            "created_at": datetime.now()
        })
        return True

    @staticmethod
    def authenticate(username: str, password: str):
        if not db: return False
        user_ref = db.collection("users").document(username).get()
        if user_ref.exists:
            user_data = user_ref.to_dict()
            if AuthService.check_password(password, user_data['password']):
                return True
        return False

# --- 3. SERVIÇOS DE DADOS E PDF ---
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

    @staticmethod
    def generate_pdf(project_name: str, data: List[Dict]):
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Helvetica', sans-serif; color: #333; }}
                    .header {{ text-align: center; border-bottom: 2px solid #2980b9; padding-bottom: 10px; }}
                    .epic {{ background: #f4f7f6; padding: 15px; margin-top: 20px; border-left: 10px solid #8e44ad; }}
                    .feat {{ margin-left: 30px; border-left: 5px solid #27ae60; padding-left: 10px; margin-top: 10px; }}
                    .item {{ margin-left: 60px; font-size: 0.9em; color: #555; }}
                    .task {{ margin-left: 90px; font-style: italic; font-size: 0.85em; color: #7f8c8d; }}
                    .badge {{ background: #eee; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Architect Pro: Snapshot de Backlog</h1>
                    <p>Projeto: {project_name} | Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
        """
        for ep in data:
            html_content += f"<div class='epic'><strong>Épico: {ep['title']}</strong> <span class='badge'>{ep['responsible']}</span>"
            for ft in ep.get('children', []):
                html_content += f"<div class='feat'><strong>Feature: {ft['title']}</strong> <span class='badge'>{ft['responsible']}</span>"
                for bk in ft.get('children', []):
                    html_content += f"<div class='item'>Item: {bk['title']} ({bk['responsible']})"
                    for tk in bk.get('children', []):
                        html_content += f"<div class='task'>Tarefa: {tk['title']} [{tk['responsible']}]</div>"
                    html_content += "</div>"
                html_content += "</div>"
            html_content += "</div>"
        
        html_content += "</body></html>"
        return HTML(string=html_content).write_pdf()

# --- 4. COMPONENTES DE UI ---
def apply_styles():
    st.markdown("""
        <style>
        .stButton > button { width: 100%; border-radius: 5px; }
        .card-info { font-size: 0.75rem; margin-top: -10px; margin-bottom: 10px; }
        .task-card { 
            padding: 10px; border-radius: 5px; 
            border-left: 5px solid #2980b9; margin-bottom: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

def edit_modal(item: Dict, key_prefix: str):
    with st.popover("📝", use_container_width=False):
        new_title = st.text_input("Título", value=item['title'], key=f"t_{key_prefix}")
        new_resp = st.text_input("Responsável", value=item['responsible'], key=f"r_{key_prefix}")
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
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Cadastro"])
        
        with tab1:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                user = st.text_input("Usuário", key="login_user")
                pw = st.text_input("Senha", type="password", key="login_pw")
                if st.button("Entrar"):
                    if AuthService.authenticate(user, pw):
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas")
        
        with tab2:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                new_user = st.text_input("Novo Usuário", key="reg_user")
                new_pw_1 = st.text_input("Nova Senha", type="password", key="reg_pw_1")
                new_pw_2 = st.text_input("Repita a Senha", type="password", key="reg_pw_2")
                if st.button("Cadastrar"):
                    if new_pw_1 == new_pw_2:
                        if AuthService.create_user(new_user, new_pw_1):
                            st.success("Conta criada! Vá para a aba de Login.")
                        else:
                            st.error("Usuário já existe.")
                    else:
                        st.error("As senhas não coincidem.")

        return

    # SIDEBAR
    with st.sidebar:
        st.title(f"🚀 {st.session_state.user}")
        if st.button("Log out"):
            st.session_state.authenticated = False
            st.rerun()
        
        st.divider()
        st.subheader("📁 Projeto Atual")

        if "proj_name" not in st.session_state:
            st.session_state.proj_name = "Meu Backlog 001"
        proj_name = st.text_input("Nome do Projeto", value=st.session_state.proj_name)
        
        if st.button("💾 Salvar"):
            if DataService.save_project(st.session_state.user, proj_name, st.session_state.backlog):
                st.success("Salvo com sucesso!")
        
        st.divider()
        st.subheader("📝 Relatórios")

        pdf_data = DataService.generate_pdf(proj_name, st.session_state.backlog)
        st.download_button(
            label="📄 Exportar Backlog",
            data=pdf_data,
            file_name=f"{proj_name}.pdf",
            mime="application/pdf"
        )

        email_destinatario = st.text_input("E-mail para envio", value=f"")

        if st.button("✨ Gerar Documentação (IA)"):
            with st.spinner("O Gemini está redigindo os PBIs..."):
                doc_pdf = DocService.generate_doc_report(proj_name, st.session_state.backlog)
                if email_destinatario != "":
                    sucesso = EmailService.send_backlog_report(email_destinatario, proj_name, st.session_state.user, doc_pdf)
                else:
                    sucesso = False

                if sucesso:
                    st.success(f"E-mail enviado para {email_destinatario}!")

                st.download_button(
                    label="📥 Baixar Relatório de PBIs",
                    data=doc_pdf,
                    file_name=f"DOC_{proj_name}.pdf",
                    mime="application/pdf"
                )

        st.divider()
        st.subheader("📂 Abrir Projeto")
        repo = DataService.get_projects(st.session_state.user)
        if repo:
            selected_load = st.selectbox("Selecione", options=list(repo.keys()))
            if st.button("📂 Carregar"):
                st.session_state.backlog = repo[selected_load]['data']
                st.session_state.proj_name = selected_load
                st.rerun()

    # DASHBOARD DE EDIÇÃO
    cols = st.columns(4)

    # 1. ÉPICOS
    with cols[0]:
        st.subheader("🟣 Épicos")
        if st.button("➕ Novo Épico"):
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

    # 2. FEATURES
    with cols[1]:
        st.subheader("🟢 Features")
        if st.session_state.sel["epic"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            if st.button("➕ Nova Feature"):
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

    # 3. ITENS DE BACKLOG
    with cols[2]:
        st.subheader("🟡 Itens")
        if st.session_state.sel["feat"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            curr_ft = next(x for x in curr_ep["children"] if x['id'] == st.session_state.sel["feat"])
            if st.button("➕ Novo Item"):
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

    # 4. TAREFAS
    with cols[3]:
        st.subheader("🔵 Tarefas")
        if st.session_state.sel["back"]:
            curr_ep = next(x for x in st.session_state.backlog if x['id'] == st.session_state.sel["epic"])
            curr_ft = next(x for x in curr_ep["children"] if x['id'] == st.session_state.sel["feat"])
            curr_bk = next(x for x in curr_ft["children"] if x['id'] == st.session_state.sel["back"])
            
            with st.popover("➕ Adicionar Tarefa", use_container_width=True):
                t = st.text_input("O que fazer?")
                r = st.text_input("Quem?")
                if st.button("Adicionar"):
                    curr_bk["children"].append({"title": t, "responsible": r})
                    st.rerun()

            for i, tk in enumerate(curr_bk["children"]):
                with st.container():
                    st.markdown(f"""
                        <div class="task-card">
                            <b>{tk['title']}</b><br>
                            <small>👤 {tk['responsible']}</small>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button("🗑️ Remover", key=f"del_t_{i}"):
                        curr_bk["children"].pop(i)
                        st.rerun()

if __name__ == "__main__":
    main()