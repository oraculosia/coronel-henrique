import streamlit as st

from src.auth.session import (
    SESSION_DEFAULTS,
    clear_session,
    get_profile,
    initialize_session,
    is_authenticated,
    set_authenticated_session,
    set_pending_verification,
)


def test_initialize_session_sets_defaults() -> None:
    initialize_session()

    for key, value in SESSION_DEFAULTS.items():
        assert st.session_state[key] == value


def test_initialize_session_does_not_overwrite_existing_values() -> None:
    initialize_session()
    st.session_state["authenticated"] = True

    initialize_session()

    assert st.session_state["authenticated"] is True


def test_set_authenticated_session_populates_state(verified_profile) -> None:
    initialize_session()

    set_authenticated_session(
        access_token="access-token",
        refresh_token="refresh-token",
        profile=verified_profile,
    )

    assert is_authenticated() is True
    assert st.session_state["access_token"] == "access-token"
    assert st.session_state["refresh_token"] == "refresh-token"
    assert st.session_state["user_id"] == verified_profile["id"]
    assert st.session_state["user_email"] == verified_profile["email"]
    assert get_profile() == verified_profile


def test_set_authenticated_session_clears_pending_verification(
    verified_profile,
) -> None:
    initialize_session()
    set_pending_verification("pendente@exemplo.com")

    set_authenticated_session(
        access_token="access-token",
        refresh_token="refresh-token",
        profile=verified_profile,
    )

    assert st.session_state["pending_verification_email"] is None


def test_set_pending_verification_stores_email() -> None:
    initialize_session()

    set_pending_verification("pendente@exemplo.com")

    assert st.session_state["pending_verification_email"] == "pendente@exemplo.com"


def test_clear_session_resets_everything(verified_profile) -> None:
    initialize_session()
    set_authenticated_session(
        access_token="access-token",
        refresh_token="refresh-token",
        profile=verified_profile,
    )

    clear_session()

    assert is_authenticated() is False
    assert get_profile() is None
    for key, value in SESSION_DEFAULTS.items():
        assert st.session_state[key] == value


def test_is_authenticated_false_by_default() -> None:
    initialize_session()
    assert is_authenticated() is False


def test_get_profile_returns_none_when_absent() -> None:
    initialize_session()
    assert get_profile() is None
