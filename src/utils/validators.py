import re

from email_validator import EmailNotValidError, validate_email


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_email_address(email: str) -> tuple[bool, str]:
    try:
        normalized = validate_email(
            email,
            check_deliverability=False,
        ).normalized
        return True, normalized
    except EmailNotValidError as error:
        return False, str(error)


def normalize_whatsapp(whatsapp: str) -> str:
    digits = re.sub(r"\D", "", whatsapp or "")

    if not digits:
        return ""

    if digits.startswith("55"):
        return f"+{digits}"

    return f"+55{digits}"


def validate_whatsapp(whatsapp: str) -> tuple[bool, str]:
    normalized = normalize_whatsapp(whatsapp)

    if not re.fullmatch(r"\+[1-9]\d{7,14}", normalized):
        return (
            False,
            "Informe um WhatsApp válido com DDD. Exemplo: (31) 99999-9999.",
        )

    return True, normalized


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."

    if not re.search(r"[A-Z]", password):
        return False, "A senha deve conter ao menos uma letra maiúscula."

    if not re.search(r"[a-z]", password):
        return False, "A senha deve conter ao menos uma letra minúscula."

    if not re.search(r"\d", password):
        return False, "A senha deve conter ao menos um número."

    return True, ""