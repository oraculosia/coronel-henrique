from functools import lru_cache

from supabase import Client, create_client

from src.config.settings import settings


def _require_foundation_url_and_keys(*, require_service_role: bool = False) -> None:
    errors = settings.foundation_errors()
    if require_service_role:
        relevant = errors
    else:
        relevant = [
            error
            for error in errors
            if "SERVICE_ROLE" not in error
        ]

    if relevant:
        raise RuntimeError(" ".join(relevant))


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    _require_foundation_url_and_keys(require_service_role=False)
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_PUBLISHABLE_KEY,
    )


@lru_cache(maxsize=1)
def get_supabase_admin() -> Client:
    _require_foundation_url_and_keys(require_service_role=True)
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
    )