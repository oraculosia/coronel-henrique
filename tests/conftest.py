from __future__ import annotations

from typing import Any

import pytest
import streamlit as st


def pytest_configure(config) -> None:  # noqa: ANN001
    config.addinivalue_line(
        "markers",
        "live: testes que exigem projeto Supabase configurado e schema aplicado",
    )


@pytest.fixture(autouse=True)
def _reset_streamlit_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


@pytest.fixture
def verified_profile() -> dict[str, Any]:
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "first_name": "William",
        "last_name": "Eustáquio",
        "email": "programador.descpro@gmail.com",
        "whatsapp": "+5531998417976",
        "job_title": "Desenvolvedor de IA",
        "avatar_path": None,
        "role": "super_admin",
        "verification_status": "verified",
        "is_active": True,
    }


@pytest.fixture
def no_auth_service_network(monkeypatch):
    """Impede que AuthService() abra uma conexão real com o Supabase."""
    from src.services.auth_service import AuthService

    monkeypatch.setattr(AuthService, "__init__", lambda self: None)
    return AuthService
