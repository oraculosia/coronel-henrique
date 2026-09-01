import streamlit as st

from src.auth.authorization import has_role
from src.auth.session import initialize_session, is_authenticated


def require_authentication() -> None:
    initialize_session()

    if not is_authenticated():
        st.warning("Faça login para acessar esta página.")
        st.switch_page("pages/05_🔐_Login.py")


def require_roles(*roles: str) -> None:
    require_authentication()

    if not has_role(*roles):
        st.error("Você não tem permissão para acessar esta página.")
        st.stop()