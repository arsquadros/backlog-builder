import streamlit as st

from google.cloud import firestore
from google.oauth2 import service_account
from weasyprint import HTML

from datetime import datetime
from typing import List, Dict


def get_firestore_client():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = service_account.Credentials.from_service_account_info(
                creds_dict
            )
            return firestore.Client(
                credentials=creds,
                project=creds_dict["project_id"]
            )
        return firestore.Client()
    except Exception as e:
        st.error(f"Erro Firestore: {e}")
        return None


db = get_firestore_client()


class DataService:
    @staticmethod
    def save_project(user_id, project_name, data):
        if not db:
            return False

        db.collection("users")\
          .document(user_id)\
          .collection("backlogs")\
          .document(project_name)\
          .set({
              "name": project_name,
              "data": data,
              "updated_at": datetime.now()
          })
        return True

    @staticmethod
    def get_projects(user_id):
        if not db:
            return {}

        docs = db.collection("users")\
                 .document(user_id)\
                 .collection("backlogs")\
                 .stream()

        return {d.id: d.to_dict() for d in docs}
    
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
    
    @staticmethod
    def delete_project(user_id, project_name):
        if not db:
            return False

        try:
            db.collection("users")\
              .document(user_id)\
              .collection("backlogs")\
              .document(project_name)\
              .delete()
            return True
        except Exception as e:
            st.error(f"Erro ao deletar projeto: {e}")
            return False
        
    @staticmethod
    def get_user_data(user_id: str) -> Dict:
        """Recupera todos os dados de perfil do usuário via UUID."""
        if not db:
            return {}
        doc = db.collection("users").document(user_id).get()
        return doc.to_dict() if doc.exists else {}
    
    @staticmethod
    def get_user_uuid(username: str) -> Dict:
        """Recupera todos os dados de perfil do usuário via UUID."""
        docs = db.collection("users").where("username", "==", username).limit(1).get()
        if not docs:
            return None
        return docs[0].to_dict().get("id")

    @staticmethod
    def update_user_data(user_id: str, data: Dict) -> bool:
        """Atualiza informações editáveis do usuário."""
        if not db:
            return False
        try:
            # Garante que não sobrescrevemos campos sensíveis por erro se não passados
            db.collection("users").document(user_id).update(data)
            return True
        except Exception as e:
            st.error(f"Erro ao atualizar perfil: {e}")
            return False