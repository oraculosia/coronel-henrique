from __future__ import annotations

import os
from urllib.parse import urlparse


ENV_ALIASES: dict[str, tuple[str, ...]] = {
    "SUPABASE_PUBLISHABLE_KEY": (
        "SUPABASE_PUBLISHABLE_KEY",
        "PUBLISHABE_KEY",
        "SUPABASE_ANON_KEY",
    ),
    "SUPABASE_SERVICE_ROLE_KEY": (
        "SUPABASE_SERVICE_ROLE_KEY",
        "SECRET_KEY",
        "SUPABASE_SECRET_KEY",
        "SUPABASE_SERVICE_KEY",
    ),
}


def getenv_aliased(name: str, default: str = "") -> str:
    for candidate in ENV_ALIASES.get(name, (name,)):
        value = os.getenv(candidate, "").strip()
        if value:
            return value
    return os.getenv(name, default).strip() or default


def is_supabase_api_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"}:
        return False
    if not parsed.netloc:
        return False
    return True


def validate_foundation_settings(
    *,
    supabase_url: str,
    publishable_key: str,
    service_role_key: str,
) -> list[str]:
    errors: list[str] = []

    if not supabase_url:
        errors.append("SUPABASE_URL não configurada.")
    elif supabase_url.startswith("postgresql://") or supabase_url.startswith("postgres://"):
        errors.append(
            "SUPABASE_URL deve ser a URL HTTPS da API "
            "(https://<ref>.supabase.co), não a connection string Postgres."
        )
    elif not is_supabase_api_url(supabase_url):
        errors.append("SUPABASE_URL inválida. Use https://<projeto>.supabase.co")

    if not publishable_key:
        errors.append("SUPABASE_PUBLISHABLE_KEY não configurada.")

    if not service_role_key:
        errors.append("SUPABASE_SERVICE_ROLE_KEY não configurada.")

    if publishable_key and service_role_key and publishable_key == service_role_key:
        errors.append(
            "A chave publicável e a service role não podem ser iguais."
        )

    return errors
