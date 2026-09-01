from functools import lru_cache

from supabase import Client, create_client

from src.config.settings import settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    if not settings.SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL não configurada no arquivo .env.")

    if not settings.SUPABASE_PUBLISHABLE_KEY:
        raise RuntimeError(
            "SUPABASE_PUBLISHABLE_KEY não configurada no arquivo .env."
        )

    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_PUBLISHABLE_KEY,
    )