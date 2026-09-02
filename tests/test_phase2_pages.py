"""Testes de aceite da Fase 2 usando streamlit.testing.v1.AppTest.

Cada teste navega a partir de app.py (necessário para st.page_link resolver
as páginas do app multipágina) e usa AuthService/monkeypatch para não
depender de rede/Supabase real.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from src.services.auth_service import AuthService, ServiceResult

ROOT_DIR = Path(__file__).resolve().parents[1]
APP_PATH = str(ROOT_DIR / "app.py")


def _make_app(monkeypatch) -> AppTest:
    monkeypatch.setattr(AuthService, "__init__", lambda self: None)
    at = AppTest.from_file(APP_PATH)
    at.run()
    return at


def _goto(at: AppTest, page: str) -> AppTest:
    at = at.switch_page(page)
    at.run()
    return at


def _input(at: AppTest, label: str):
    return next(ti for ti in at.text_input if ti.label == label)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def test_login_page_renders_form(monkeypatch) -> None:
    at = _make_app(monkeypatch)
    at = _goto(at, "pages/05_🔐_Login.py")

    assert not at.exception
    labels = [ti.label for ti in at.text_input]
    assert "E-mail" in labels
    assert "Senha" in labels


def test_login_invalid_credentials_shows_error(monkeypatch) -> None:
    monkeypatch.setattr(
        AuthService,
        "sign_in",
        lambda self, email, password: ServiceResult(
            success=False, message="E-mail ou senha inválidos."
        ),
    )
    at = _make_app(monkeypatch)
    at = _goto(at, "pages/05_🔐_Login.py")

    at.text_input[0].input("desconhecido@exemplo.com")
    at.text_input[1].input("SenhaErrada1")
    at.button[0].click()
    at.run()

    assert [e.value for e in at.error] == ["E-mail ou senha inválidos."]


def test_login_success_redirects_home(monkeypatch, verified_profile) -> None:
    monkeypatch.setattr(
        AuthService,
        "sign_in",
        lambda self, email, password: ServiceResult(
            success=True,
            message="ok",
            data={
                "user_id": verified_profile["id"],
                "email": verified_profile["email"],
                "access_token": "access-token",
                "refresh_token": "refresh-token",
            },
        ),
    )
    monkeypatch.setattr(
        AuthService,
        "get_profile",
        lambda self, user_id, access_token: ServiceResult(
            success=True, message="ok", data=verified_profile
        ),
    )

    at = _make_app(monkeypatch)
    at = _goto(at, "pages/05_🔐_Login.py")

    at.text_input[0].input(verified_profile["email"])
    at.text_input[1].input("William@2026")
    at.button[0].click()
    at.run()

    assert at.session_state["authenticated"] is True
    assert at.session_state["profile"] == verified_profile


def test_login_pending_verification_warns_user(monkeypatch, verified_profile) -> None:
    pending_profile = {**verified_profile, "verification_status": "pending"}
    monkeypatch.setattr(
        AuthService,
        "sign_in",
        lambda self, email, password: ServiceResult(
            success=True,
            message="ok",
            data={
                "user_id": pending_profile["id"],
                "email": pending_profile["email"],
                "access_token": "access-token",
                "refresh_token": "refresh-token",
            },
        ),
    )
    monkeypatch.setattr(
        AuthService,
        "get_profile",
        lambda self, user_id, access_token: ServiceResult(
            success=True, message="ok", data=pending_profile
        ),
    )

    at = _make_app(monkeypatch)
    at = _goto(at, "pages/05_🔐_Login.py")

    at.text_input[0].input(pending_profile["email"])
    at.text_input[1].input("William@2026")
    at.button[0].click()
    at.run()

    assert at.session_state["authenticated"] is False
    assert any("não foi confirmado" in w.value for w in at.warning)


# ---------------------------------------------------------------------------
# Cadastro
# ---------------------------------------------------------------------------


def test_signup_page_validation_blocks_mismatched_passwords(monkeypatch) -> None:
    at = _make_app(monkeypatch)
    at = _goto(at, "pages/06_📝_Criar_Conta.py")

    _input(at, "Nome").input("William")
    _input(at, "Sobrenome").input("Eustáquio")
    _input(at, "E-mail").input("programador.descpro@gmail.com")
    _input(at, "WhatsApp").input("31998417976")
    _input(at, "Senha").input("William@2026")
    _input(at, "Confirmar senha").input("Outra@2026")
    at.checkbox[0].check()
    at.button[0].click()
    at.run()

    assert any("confirmação" in e.value.lower() for e in at.error)


def test_signup_page_success_stores_pending_verification(monkeypatch) -> None:
    monkeypatch.setattr(
        AuthService,
        "sign_up",
        lambda self, **kwargs: ServiceResult(
            success=True,
            message="ok",
            data={
                "user_id": "user-1",
                "email": "programador.descpro@gmail.com",
                "session_exists": False,
            },
        ),
    )
    monkeypatch.setattr(
        AuthService,
        "send_verification_code",
        lambda self, **kwargs: ServiceResult(success=True, message="ok"),
    )

    at = _make_app(monkeypatch)
    at = _goto(at, "pages/06_📝_Criar_Conta.py")

    _input(at, "Nome").input("William")
    _input(at, "Sobrenome").input("Eustáquio")
    _input(at, "E-mail").input("programador.descpro@gmail.com")
    _input(at, "WhatsApp").input("31998417976")
    _input(at, "Senha").input("William@2026")
    _input(at, "Confirmar senha").input("William@2026")
    _input(at, "Cargo").input("Desenvolvedor de IA")
    at.checkbox[0].check()
    at.button[0].click()
    at.run()

    assert not at.exception
    assert (
        at.session_state["pending_verification_email"]
        == "programador.descpro@gmail.com"
    )


# ---------------------------------------------------------------------------
# Verificação por OTP
# ---------------------------------------------------------------------------


def test_otp_page_rejects_short_code(monkeypatch) -> None:
    at = _make_app(monkeypatch)
    at = _goto(at, "pages/07_✅_Verificar_Email.py")

    at.text_input[0].input("programador.descpro@gmail.com")
    at.text_input[1].input("123")
    at.button[0].click()
    at.run()

    assert any("código recebido" in e.value.lower() for e in at.error)


def test_otp_page_success_without_tokens_shows_login_link(
    monkeypatch, verified_profile
) -> None:
    monkeypatch.setattr(
        AuthService,
        "verify_own_code",
        lambda self, email, code: ServiceResult(
            success=True,
            message="ok",
            data={"user_id": verified_profile["id"], "email": verified_profile["email"]},
        ),
    )

    at = _make_app(monkeypatch)
    at = _goto(at, "pages/07_✅_Verificar_Email.py")

    at.text_input[0].input(verified_profile["email"])
    at.text_input[1].input("123456")
    at.button[0].click()
    at.run()

    assert not at.exception
    assert at.session_state["authenticated"] is False
    assert any("confirmado" in s.value.lower() for s in at.success)


def test_otp_page_success_with_tokens_authenticates_user(
    monkeypatch, verified_profile
) -> None:
    monkeypatch.setattr(
        AuthService,
        "verify_own_code",
        lambda self, email, code: ServiceResult(
            success=True,
            message="ok",
            data={"user_id": verified_profile["id"], "email": verified_profile["email"]},
        ),
    )
    monkeypatch.setattr(
        AuthService,
        "get_profile",
        lambda self, user_id, access_token: ServiceResult(
            success=True, message="ok", data=verified_profile
        ),
    )

    at = _make_app(monkeypatch)
    at = _goto(at, "pages/07_✅_Verificar_Email.py")
    at.session_state["pending_verification_tokens"] = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
    }

    at.text_input[0].input(verified_profile["email"])
    at.text_input[1].input("123456")
    at.button[0].click()
    at.run()

    assert at.session_state["authenticated"] is True
    assert at.session_state["profile"] == verified_profile


def test_otp_page_invalid_code_shows_error(monkeypatch) -> None:
    monkeypatch.setattr(
        AuthService,
        "verify_own_code",
        lambda self, email, code: ServiceResult(
            success=False, message="Código inválido ou expirado."
        ),
    )

    at = _make_app(monkeypatch)
    at = _goto(at, "pages/07_✅_Verificar_Email.py")

    at.text_input[0].input("programador.descpro@gmail.com")
    at.text_input[1].input("000000")
    at.button[0].click()
    at.run()

    assert any("Código inválido" in e.value for e in at.error)


# ---------------------------------------------------------------------------
# Guards: página protegida redireciona quando não autenticado
# ---------------------------------------------------------------------------


def test_protected_page_redirects_anonymous_user(monkeypatch) -> None:
    at = _make_app(monkeypatch)
    at = _goto(at, "pages/08_👤_Minha_Conta.py")

    assert at.session_state["authenticated"] is False


# ---------------------------------------------------------------------------
# Minha Conta
# ---------------------------------------------------------------------------


def _login_as(at: AppTest, profile: dict[str, Any]) -> None:
    at.session_state["authenticated"] = True
    at.session_state["access_token"] = "access-token"
    at.session_state["refresh_token"] = "refresh-token"
    at.session_state["user_id"] = profile["id"]
    at.session_state["user_email"] = profile["email"]
    at.session_state["profile"] = profile


def test_account_page_prefills_current_profile(monkeypatch, verified_profile) -> None:
    at = _make_app(monkeypatch)
    _login_as(at, verified_profile)
    at = _goto(at, "pages/08_👤_Minha_Conta.py")

    values = {ti.label: ti.value for ti in at.text_input}
    assert values["Nome"] == verified_profile["first_name"]
    assert values["Cargo"] == verified_profile["job_title"]
    assert values["Tipo de acesso"] == "Administração"


def test_account_page_role_field_is_disabled(monkeypatch, verified_profile) -> None:
    at = _make_app(monkeypatch)
    _login_as(at, verified_profile)
    at = _goto(at, "pages/08_👤_Minha_Conta.py")

    role_input = next(ti for ti in at.text_input if ti.label == "Tipo de acesso")
    email_input = next(ti for ti in at.text_input if ti.label == "E-mail")
    assert role_input.disabled is True
    assert email_input.disabled is True


def test_account_page_updates_profile(monkeypatch, verified_profile) -> None:
    updated_profile = {**verified_profile, "job_title": "Head de IA"}
    monkeypatch.setattr(
        AuthService,
        "update_own_profile",
        lambda self, **kwargs: ServiceResult(
            success=True, message="ok", data=updated_profile
        ),
    )

    # st.rerun() encerra o script logo apos o sucesso; sem isso a mensagem
    # de sucesso nao sobreviveria para ser inspecionada neste teste.
    monkeypatch.setattr("streamlit.rerun", lambda: None)

    at = _make_app(monkeypatch)
    _login_as(at, verified_profile)
    at = _goto(at, "pages/08_👤_Minha_Conta.py")

    job_title_input = next(ti for ti in at.text_input if ti.label == "Cargo")
    job_title_input.input("Head de IA")
    at.button[0].click()
    at.run()

    assert not at.exception
    assert at.session_state["profile"]["job_title"] == "Head de IA"
    assert any("atualizados" in s.value for s in at.success)


def test_account_page_rejects_mismatched_new_password(
    monkeypatch, verified_profile
) -> None:
    at = _make_app(monkeypatch)
    _login_as(at, verified_profile)
    at = _goto(at, "pages/08_👤_Minha_Conta.py")

    new_password_input = next(
        ti for ti in at.text_input if ti.label == "Nova senha"
    )
    confirm_password_input = next(
        ti for ti in at.text_input if ti.label == "Confirmar nova senha"
    )
    new_password_input.input("Nova@2026")
    confirm_password_input.input("Diferente@2026")
    at.button[0].click()
    at.run()

    assert any("não corresponde" in e.value for e in at.error)
