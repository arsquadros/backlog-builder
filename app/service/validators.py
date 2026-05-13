import re


def is_valid_username(username):
    pattern = r"^[a-zA-Z][a-zA-Z0-9_]{2,19}$"
    ok = re.match(pattern, username)

    if not ok:
        return False, "Usuário inválido"

    return True, ""


def is_valid_password(password):
    if len(password) < 8:
        return False, "Senha muito curta"

    if not re.search(r"[A-Z]", password):
        return False, "Precisa de maiúscula"

    if not re.search(r"\d", password):
        return False, "Precisa de número"

    return True, ""


def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    ok = re.match(pattern, email)
    if not ok:
        return False, "E-mail inválido"
    return True, ""
