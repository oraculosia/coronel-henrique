import streamlit as st

from src.auth.authorization import has_role
from src.auth.session import (
    clear_session,
    initialize_session,
    is_access_token_expired,
    is_authenticated,
    update_tokens,
)
from src.database.supabase_client import get_supabase


def require_authentication() -> None:
    initialize_session()

    if not is_authenticated():
        st.warning("Faça login para acessar esta página.")
        st.switch_page("pages/05_🔐_Login.py")
        return

    ensure_fresh_access_token()


def ensure_fresh_access_token() -> None:
    """Renova o access_token via refresh_token quando ele expira — sem isso,
    toda query protegida por RLS (parceiros, apoiadores, metas) passava a
    falhar silenciosamente com mensagem genérica após ~1h de sessão aberta."""
    access_token = st.session_state.get("access_token")
    if not is_access_token_expired(access_token):
        return

    refresh_token = st.session_state.get("refresh_token")
    if not refresh_token:
        clear_session()
        st.warning("Sua sessão expirou. Faça login novamente.")
        st.switch_page("pages/05_🔐_Login.py")
        return

    try:
        client = get_supabase()
        result = client.auth.refresh_session(refresh_token)
        new_session = result.session
        if not new_session:
            raise ValueError("Refresh sem sessão retornada.")
        update_tokens(new_session.access_token, new_session.refresh_token)
    except Exception:
        clear_session()
        st.warning("Sua sessão expirou. Faça login novamente.")
        st.switch_page("pages/05_🔐_Login.py")


def require_roles(*roles: str) -> None:
    require_authentication()

    if not has_role(*roles):
        st.error("Você não tem permissão para acessar esta página.")
        st.stop()