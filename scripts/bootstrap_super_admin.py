"""Cria ou promove o primeiro super_admin de forma controlada.

Uso (com .venv ativo):

    python scripts/bootstrap_super_admin.py

Requer no .env:
    SUPABASE_URL
    SUPABASE_PUBLISHABLE_KEY
    SUPABASE_SERVICE_ROLE_KEY
    SUPER_ADMIN_EMAIL
    SUPER_ADMIN_PASSWORD
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config.settings import settings  # noqa: E402
from src.database.supabase_client import get_supabase_admin  # noqa: E402
from src.utils.validators import (  # noqa: E402
    validate_email_address,
    validate_password,
    validate_whatsapp,
)


def main() -> int:
    email_ok, email_result = validate_email_address(settings.SUPER_ADMIN_EMAIL)
    password_ok, password_message = validate_password(settings.SUPER_ADMIN_PASSWORD)

    if not email_ok:
        print(f"SUPER_ADMIN_EMAIL inválido: {email_result}")
        return 1

    if not password_ok:
        print(f"SUPER_ADMIN_PASSWORD inválida: {password_message}")
        return 1

    whatsapp_ok, whatsapp_result = validate_whatsapp(settings.SUPER_ADMIN_WHATSAPP)
    if not whatsapp_ok:
        print(f"SUPER_ADMIN_WHATSAPP inválido: {whatsapp_result}")
        return 1

    issues = settings.foundation_errors()
    if issues:
        print("Fundação incompleta:")
        for issue in issues:
            print(f" - {issue}")
        return 1

    admin = get_supabase_admin()

    try:
        admin.table("profiles").select("id, job_title").limit(1).execute()
    except Exception as error:
        detail = str(error)
        if "job_title" in detail:
            print(
                "Schema desatualizado: a coluna profiles.job_title não existe.\n"
                "No SQL Editor do Supabase, execute sql/003_profile_job_title.sql\n"
                "e rode este script novamente."
            )
            return 1
        print(f"Não foi possível ler public.profiles: {error}")
        print("Aplique sql/001_foundation.sql no SQL Editor e tente novamente.")
        return 1

    created = False
    user_id: str | None = None

    try:
        response = admin.auth.admin.create_user(
            {
                "email": email_result,
                "password": settings.SUPER_ADMIN_PASSWORD,
                "email_confirm": True,
                "user_metadata": {
                    "first_name": settings.SUPER_ADMIN_FIRST_NAME,
                    "last_name": settings.SUPER_ADMIN_LAST_NAME,
                    "whatsapp": whatsapp_result,
                    "job_title": settings.SUPER_ADMIN_JOB_TITLE,
                },
            }
        )
        user_id = str(response.user.id) if response.user else None
        created = True
    except Exception as error:
        message = str(error).lower()
        already_exists = any(
            token in message
            for token in ("already", "registered", "exists", "duplicate")
        )
        if "database error creating new user" in message:
            print(
                "Falha ao criar usuário: o trigger de profiles recusou o insert.\n"
                "Causa mais comum: coluna job_title ausente.\n"
                "Execute sql/003_profile_job_title.sql no SQL Editor e tente de novo."
            )
            return 1
        if not already_exists:
            print(f"Falha ao criar usuário: {error}")
            return 1

        listed = admin.auth.admin.list_users()
        users = getattr(listed, "users", listed) or []
        for user in users:
            if str(getattr(user, "email", "")).lower() == email_result:
                user_id = str(user.id)
                break

        if not user_id:
            print("Usuário já existe, mas não foi possível localizar o id.")
            return 1

    update = (
        admin.table("profiles")
        .update(
            {
                "first_name": settings.SUPER_ADMIN_FIRST_NAME,
                "last_name": settings.SUPER_ADMIN_LAST_NAME,
                "whatsapp": whatsapp_result,
                "job_title": settings.SUPER_ADMIN_JOB_TITLE,
                "role": "super_admin",
                "verification_status": "verified",
                "is_active": True,
                "email": email_result,
            }
        )
        .eq("id", user_id)
        .execute()
    )

    if not update.data:
        print(
            "Usuário Auth criado, mas o perfil não foi atualizado. "
            "Aplique sql/001_foundation.sql e tente novamente."
        )
        return 1

    action = "criado e promovido" if created else "promovido"
    print(f"super_admin {action}: {email_result}")
    print(
        f"{settings.SUPER_ADMIN_FIRST_NAME} {settings.SUPER_ADMIN_LAST_NAME} "
        f"| cargo: {settings.SUPER_ADMIN_JOB_TITLE} | papel: super_admin"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
