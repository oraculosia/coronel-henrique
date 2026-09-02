from typing import Any

import streamlit as st


SESSION_DEFAULTS: dict[str, Any] = {
    "authenticated": False,
    "access_token": None,
    "refresh_token": None,
    "user_id": None,
    "user_email": None,
    "profile": None,
    "pending_verification_email": None,
    "pending_verification_tokens": None,
}


def initialize_session() -> None:
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_authenticated_session(
    access_token: str,
    refresh_token: str,
    profile: dict[str, Any],
) -> None:
    st.session_state["authenticated"] = True
    st.session_state["access_token"] = access_token
    st.session_state["refresh_token"] = refresh_token
    st.session_state["user_id"] = profile["id"]
    st.session_state["user_email"] = profile["email"]
    st.session_state["profile"] = profile
    st.session_state["pending_verification_email"] = None
    st.session_state["pending_verification_tokens"] = None


def set_pending_verification(
    email: str,
    access_token: str | None = None,
    refresh_token: str | None = None,
) -> None:
    """Guarda o e-mail pendente e, se disponível, a sessão já emitida no
    sign_up (usada para logar automaticamente após o código próprio ser
    confirmado, sem precisar pedir a senha de novo)."""
    st.session_state["pending_verification_email"] = email
    st.session_state["pending_verification_tokens"] = (
        {"access_token": access_token, "refresh_token": refresh_token}
        if access_token and refresh_token
        else None
    )


def clear_session() -> None:
    for key, value in SESSION_DEFAULTS.items():
        st.session_state[key] = value


def get_profile() -> dict[str, Any] | None:
    return st.session_state.get("profile")


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated", False))