import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

class EmailService:
    
    @staticmethod
    def _send_email(to_email, subject, body_text, attachment_data=None, attachment_name=None):
        """Método auxiliar interno para envio de e-mails."""
        smtp_server = st.secrets["mail_service"]["smtp_server"]
        smtp_port = st.secrets["mail_service"]["smtp_port"]
        sender_email = st.secrets["mail_service"]["sender_email"]
        sender_password = st.secrets["mail_service"]["sender_password"]

        msg = MIMEMultipart()
        msg['From'] = f"Architect Pro <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body_text, 'plain'))

        if attachment_data and attachment_name:
            part = MIMEApplication(attachment_data, Name=attachment_name)
            part['Content-Disposition'] = f'attachment; filename="{attachment_name}"'
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

    @staticmethod
    def send_ai_backlog_report(user_data, project_name, pdf_data):
        """Envia o relatório de backlog gerado por IA."""
        nome = user_data.get('name', user_data.get('username'))
        to_email = user_data.get('email')
        
        remaining_reports = 5 - user_data.get('ai_generations')
        text_remaining_reports = ""
        if remaining_reports == 0:
            text_remaining_reports = "Note que você atingiu o limite de relatórios de IA de hoje, mas não se preocupe! Amanhã seu limite será reiniciado."
        else:
            text_remaining_reports = f"Note que você ainda pode gerar {remaining_reports} relatórios de IA por hoje."

        subject = f"Documentação de IA do Projeto: {project_name}"
        body = f"Olá, {nome}.\n\n" \
               f"A sua documentação técnica gerada por IA para o projeto '{project_name}' está pronta!\n" \
               f"O documento em anexo contém os templates de descrições de todos os PBIs criados neste projeto. {text_remaining_reports}\n\n" \
               "Atenciosamente,\nEquipe Architect Pro"
               
        return EmailService._send_email(to_email, subject, body, pdf_data, f"{project_name}.pdf")
    
    @staticmethod
    def send_basic_backlog_report(user_data, project_name, pdf_data):
        """Envia o relatório de backlog básico."""
        nome = user_data.get('name', user_data.get('username'))
        to_email = user_data.get('email')
        
        subject = f"Backlog em PDF do Projeto: {project_name}"
        body = f"Olá, {nome}.\n\n" \
               f"O seu backlog em PDF do projeto '{project_name}' está pronto!\n" \
               f"O documento em anexo contém tudo que você construiu na nossa plataforma.\n\n" \
               "Atenciosamente,\nEquipe Architect Pro"
               
        return EmailService._send_email(to_email, subject, body, pdf_data, f"{project_name}.pdf")

    @staticmethod
    def send_verification_code(user_data, code, action="registo"):
        """Envia o código de verificação para registo ou alteração de e-mail."""
        nome = user_data.get('name', user_data.get('username'))
        to_email = user_data.get('email')
        
        context_msg = "ativar a sua conta" if action == "registo" else "confirmar a alteração do seu e-mail"
        
        subject = "O seu código de verificação - Architect Pro"
        body = f"Olá, {nome}.\n\n" \
               f"O seu código de verificação é: {code}\n\n" \
               f"Insira este código na plataforma para {context_msg}.\n\n" \
               "Se não solicitou este código, por favor, ignore esta mensagem.\n\n" \
               "Atenciosamente,\nEquipe Architect Pro"
               
        return EmailService._send_email(to_email, subject, body)

    @staticmethod
    def send_welcome_email(user_data):
        """Confirmação de conta criada com sucesso."""
        nome = user_data.get('name', user_data.get('username'))
        to_email = user_data.get('email')
        
        subject = "Bem-vindo ao Architect Pro!"
        body = f"Olá, {nome}.\n\n" \
               "A sua conta foi criada com sucesso! Bem-vindo ao Architect Pro.\n\n" \
               "A partir de agora, pode estruturar épicos, features e tarefas, além de gerar documentações completas utilizando Inteligência Artificial para os seus projetos.\n\n" \
               "Desejamos-lhe um excelente trabalho!\n\n" \
               "Atenciosamente,\nEquipe Architect Pro"
               
        return EmailService._send_email(to_email, subject, body)

    @staticmethod
    def send_password_change_confirmation(user_data):
        """Alerta de segurança sobre a alteração de senha."""
        nome = user_data.get('name', user_data.get('username'))
        to_email = user_data.get('email')
        
        subject = "Confirmação de Alteração de Senha - Architect Pro"
        body = f"Olá, {nome}.\n\n" \
               "Informamos que a senha da sua conta no Architect Pro foi alterada.\n\n" \
               "Se não realizou esta alteração, por favor, contate imediatamente o nosso suporte técnico para proteger a sua conta.\n\n" \
               "Atenciosamente,\nEquipe Architect Pro"
               
        return EmailService._send_email(to_email, subject, body)

    @staticmethod
    def send_account_deletion_confirmation(user_data):
        """Confirmação da eliminação permanente da conta e dados."""
        nome = user_data.get('name', user_data.get('username'))
        to_email = user_data.get('email')
        
        subject = "Confirmação de Eliminação de Conta - Architect Pro"
        body = f"Olá, {nome}.\n\n" \
               "Confirmamos que a sua conta no Architect Pro e todos os dados associados (incluindo backlogs) foram removidos permanentemente dos nossos sistemas, conforme solicitado.\n\n" \
               "Lamentamos vê-lo partir. Caso deseje acessar o sistema no futuro, será necessário realizar um novo registo.\n\n" \
               "Atenciosamente,\nEquipe Architect Pro"
               
        return EmailService._send_email(to_email, subject, body)
    