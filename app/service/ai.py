import streamlit as st

from google import genai
from google.genai import types

from datetime import datetime
from app.service.db import db


class AIService:
    @staticmethod
    def generate_pbi_description(epic_title, feat_title, item_title, tasks):
        try:
            client = genai.Client(api_key=st.secrets["gcp_models"]["google_api_key"])
            task_list = ", ".join([t['title'] for t in tasks])
            
            prompt = open("app/static/pbi_description.md", "r").read().format(
                epic_title=epic_title,
                feat_title=feat_title,
                item_title=item_title,
                task_list=task_list
            )

            response = client.models.generate_content(
                model=st.secrets["gcp_models"]["google_model_name"],
                contents=types.Part.from_text(text=prompt),
                config=types.GenerateContentConfig(
                    temperature=0.5
                ),
            )
            client.close()
            return response.text
        except Exception as e:
            return f"Erro ao gerar descrição via IA. Verifique a chave de API. {e}"
        
    @staticmethod
    def can_generate_ai_report(user_id, limit_per_day=5):
        ref = db.collection("users").document(user_id)
        user_doc = ref.get()
        
        if not user_doc.exists:
            return False, "Usuário não encontrado."
            
        data = user_doc.to_dict()
        
        # Pega estado atual
        now = datetime.now()
        # Fallback para o datetime.now() se o campo não existir em usuários antigos
        last_reset = data.get("ai_last_reset", now)
        # Firestore pode retornar timezone-aware. Removendo tzinfo para simplificar diferença de horas.
        last_reset = last_reset.replace(tzinfo=None) 
        count = data.get("ai_generations", 0)

        # Reseta se já se passaram 24 horas
        if (now - last_reset).total_seconds() >= 86400: # 24 horas
            count = 0
            last_reset = now

        if count >= limit_per_day:
            return False, f"Limite de {limit_per_day} gerações diárias atingido. Amanhã seu limite será reiniciado!"

        # Incrementa o uso
        ref.update({
            "ai_generations": count + 1,
            "ai_last_reset": last_reset
        })
        
        return True, ""