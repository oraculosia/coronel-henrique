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


def set_pending_verification(email: str) -> None:
    st.session_state["pending_verification_email"] = email


def clear_session() -> None:
    for key, value in SESSION_DEFAULTS.items():
        st.session_state[key] = value


def get_profile() -> dict[str, Any] | None:
    return st.session_state.get("profile")


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated", False))