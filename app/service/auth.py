import bcrypt
import uuid
import secrets

from datetime import datetime
from app.service.db import db


class AuthService:

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

    @staticmethod
    def check_password(password, hashed):
        return bcrypt.checkpw(
            password.encode(),
            hashed.encode()
        )

    @staticmethod
    def create_user(username, password, name, email):
        # Verifica se o username já existe via query
        existing = db.collection("users").where("username", "==", username).limit(1).get()
        if len(existing) > 0:
            return False

        user_id = str(uuid.uuid4()) # Novo padrão de ID
        ref = db.collection("users").document(user_id)

        ref.set({
            "id": user_id,
            "username": username,
            "name": name,
            "email": email,
            "password": AuthService.hash_password(password),
            "created_at": datetime.now(),
            "ai_generations": 0,
            "ai_last_reset": datetime.now()
        })
        return True

    @staticmethod
    def authenticate(username, password):
        # Busca pelo campo username em vez do ID do documento
        docs = db.collection("users").where("username", "==", username).limit(1).get()

        if not docs:
            return False

        user_doc = docs[0]
        data = user_doc.to_dict()
        
        if AuthService.check_password(password, data["password"]):
            # Retornamos o UUID para ser armazenado na sessão
            return data["id"] 
        return False
        
    @staticmethod
    def request_registration(username, password, name, email):
        existing = db.collection("users").where("username", "==", username).limit(1).get()
        if existing:
            return False, "Usuário já existe."
            
        user_id = uuid.uuid4().hex
        code = str(secrets.randbelow(900000) + 100000)
        
        # Salva em uma coleção temporária
        db.collection("pending_users").document(username).set({
            "id": user_id,
            "username": username,
            "name": name,
            "email": email,
            "password": AuthService.hash_password(password),
            "verification_code": code,
            "created_at": datetime.now()
        })
        
        return True, code

    @staticmethod
    def confirm_registration(username, code_input):
        ref_pending = db.collection("pending_users").document(username)
        doc = ref_pending.get()
        
        if not doc.exists:
            return False, "Solicitação de cadastro não encontrada."
            
        data = doc.to_dict()
        if data["verification_code"] != code_input:
            return False, "Código inválido."
        
        # Move para a coleção oficial incluindo limites de IA (Requisito 4)
        db.collection("users").document(data["id"]).set({
            "id": data["id"],
            "username": username,
            "name": data["name"],
            "email": data["email"],
            "password": data["password"],
            "created_at": data["created_at"],
            "ai_generations": 0,
            "ai_last_reset": datetime.now()
        })
        
        # Limpa o cadastro temporário
        ref_pending.delete()
        return True, "Conta criada com sucesso."
    
    @staticmethod
    def update_account(user_id, new_name=None, new_password=None):
        ref = db.collection("pending_email_updates").document(user_id)
        doc = ref.get()

        if not doc.exists:
            return False
        
        updates = {}
        if new_name:
            updates["name"] = new_name
        if new_password:
            updates["password"] = AuthService.hash_password(new_password)
            
        if updates:
            doc.update(updates)
        return True

    @staticmethod
    def delete_account(user_id):
        ref = db.collection("users").document(user_id)
        doc = ref.get()
        
        if not doc.exists:
            return False, "Nenhuma solicitação de alteração encontrada."

        try:
            backlogs = ref.collection("backlogs").stream()
            for b in backlogs:
                b.reference.delete()
        except Exception as e:
            print(f"Could not delete backlogs: {e}")
        # Deletar o documento do usuário
        ref.delete()

        return True
    
    @staticmethod
    def request_email_update(user_id, new_email):
        """Gera um código para validar a troca de e-mail."""
        code = str(secrets.randbelow(900000) + 100000)
        
        # Armazena a solicitação pendente
        db.collection("pending_email_updates").document(user_id).set({
            "new_email": new_email,
            "verification_code": code,
            "requested_at": datetime.now()
        })
        return code

    @staticmethod
    def confirm_email_update(user_id, code_input):
        """Valida o código e efetiva a troca do e-mail no perfil."""
        ref_pending = db.collection("pending_email_updates").document(user_id)
        doc = ref_pending.get()
        
        if not doc.exists:
            return False, "Nenhuma solicitação de alteração encontrada."
            
        data = doc.to_dict()
        if data["verification_code"] != code_input:
            return False, "Código de verificação incorreto."
            
        # Atualiza o e-mail oficial do usuário
        db.collection("users").document(user_id).update({
            "email": data["new_email"]
        })
        
        ref_pending.delete()
        return True, "E-mail atualizado com sucesso!"
    