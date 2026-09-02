from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from supabase_auth.errors import AuthApiError

from src.services.auth_service import AuthService


@pytest.fixture
def fake_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(monkeypatch, fake_client: MagicMock) -> AuthService:
    monkeypatch.setattr(
        "src.services.auth_service.get_supabase",
        lambda: fake_client,
    )
    return AuthService()


def test_sign_up_success(service: AuthService, fake_client: MagicMock) -> None:
    fake_client.auth.sign_up.return_value = SimpleNamespace(
        user=SimpleNamespace(id="user-1"),
        session=None,
    )

    result = service.sign_up(
        first_name="William",
        last_name="Eustáquio",
        email="Programador.Descpro@gmail.com",
        whatsapp="+5531998417976",
        password="William@2026",
    )

    assert result.success
    assert result.data == {
        "user_id": "user-1",
        "email": "programador.descpro@gmail.com",
        "session_exists": False,
    }
    called_payload = fake_client.auth.sign_up.call_args.args[0]
    assert called_payload["email"] == "programador.descpro@gmail.com"
    assert called_payload["options"]["data"]["whatsapp"] == "+5531998417976"


def test_sign_up_without_user_fails(service: AuthService, fake_client: MagicMock) -> None:
    fake_client.auth.sign_up.return_value = SimpleNamespace(user=None, session=None)

    result = service.sign_up(
        first_name="A",
        last_name="B",
        email="a@b.com",
        whatsapp="+5531998417976",
        password="Abcdef12",
    )

    assert not result.success


def test_sign_up_translates_already_registered_error(
    service: AuthService, fake_client: MagicMock
) -> None:
    fake_client.auth.sign_up.side_effect = AuthApiError(
        "User already registered", 400, "user_already_exists"
    )

    result = service.sign_up(
        first_name="A",
        last_name="B",
        email="a@b.com",
        whatsapp="+5531998417976",
        password="Abcdef12",
    )

    assert not result.success
    assert result.message == "Este e-mail já possui cadastro."


def test_sign_up_generic_exception_returns_friendly_message(
    service: AuthService, fake_client: MagicMock
) -> None:
    fake_client.auth.sign_up.side_effect = RuntimeError("boom")

    result = service.sign_up(
        first_name="A",
        last_name="B",
        email="a@b.com",
        whatsapp="+5531998417976",
        password="Abcdef12",
    )

    assert not result.success
    assert "Supabase" in result.message


def test_verify_signup_otp_success(service: AuthService, fake_client: MagicMock) -> None:
    fake_client.auth.verify_otp.return_value = SimpleNamespace(
        user=SimpleNamespace(id="user-1", email="a@b.com"),
        session=SimpleNamespace(
            access_token="access-token", refresh_token="refresh-token"
        ),
    )

    result = service.verify_signup_otp(email="a@b.com", token="123456")

    assert result.success
    assert result.data == {
        "user_id": "user-1",
        "email": "a@b.com",
        "access_token": "access-token",
        "refresh_token": "refresh-token",
    }


def test_verify_signup_otp_invalid_token(
    service: AuthService, fake_client: MagicMock
) -> None:
    fake_client.auth.verify_otp.side_effect = AuthApiError(
        "Token has expired or is invalid", 403, "otp_expired"
    )

    result = service.verify_signup_otp(email="a@b.com", token="000000")

    assert not result.success
    assert "Código inválido" in result.message


def test_sign_in_success(service: AuthService, fake_client: MagicMock) -> None:
    fake_client.auth.sign_in_with_password.return_value = SimpleNamespace(
        user=SimpleNamespace(id="user-1", email="a@b.com"),
        session=SimpleNamespace(
            access_token="access-token", refresh_token="refresh-token"
        ),
    )

    result = service.sign_in(email="a@b.com", password="Abcdef12")

    assert result.success
    assert result.data["access_token"] == "access-token"


def test_sign_in_invalid_credentials(
    service: AuthService, fake_client: MagicMock
) -> None:
    fake_client.auth.sign_in_with_password.side_effect = AuthApiError(
        "Invalid login credentials", 400, "invalid_credentials"
    )

    result = service.sign_in(email="a@b.com", password="wrong")

    assert not result.success
    assert "inválidos" in result.message


def test_get_profile_success(
    monkeypatch, verified_profile, fake_client: MagicMock
) -> None:
    monkeypatch.setattr(
        "src.services.auth_service.get_supabase",
        lambda: fake_client,
    )
    execute_mock = fake_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute
    execute_mock.return_value = SimpleNamespace(data=verified_profile)

    service = AuthService()
    result = service.get_profile(user_id=verified_profile["id"], access_token="token")

    assert result.success
    assert result.data == verified_profile
    fake_client.postgrest.auth.assert_called_once_with("token")


def test_get_profile_not_found(monkeypatch, fake_client: MagicMock) -> None:
    monkeypatch.setattr(
        "src.services.auth_service.get_supabase",
        lambda: fake_client,
    )
    execute_mock = fake_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute
    execute_mock.return_value = SimpleNamespace(data=None)

    service = AuthService()
    result = service.get_profile(user_id="missing", access_token="token")

    assert not result.success


def test_update_own_profile_success(
    monkeypatch, verified_profile, fake_client: MagicMock
) -> None:
    monkeypatch.setattr(
        "src.services.auth_service.get_supabase",
        lambda: fake_client,
    )
    update_execute = fake_client.table.return_value.update.return_value.eq.return_value.execute
    update_execute.return_value = SimpleNamespace(data=[{"id": verified_profile["id"]}])

    select_execute = fake_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute
    select_execute.return_value = SimpleNamespace(data=verified_profile)

    service = AuthService()
    result = service.update_own_profile(
        access_token="token",
        user_id=verified_profile["id"],
        first_name="William",
        last_name="Eustáquio",
        whatsapp="+5531998417976",
        job_title="Desenvolvedor de IA",
    )

    assert result.success
    assert result.data == verified_profile


def test_update_own_profile_failure_when_no_rows_updated(
    monkeypatch, fake_client: MagicMock
) -> None:
    monkeypatch.setattr(
        "src.services.auth_service.get_supabase",
        lambda: fake_client,
    )
    update_execute = fake_client.table.return_value.update.return_value.eq.return_value.execute
    update_execute.return_value = SimpleNamespace(data=[])

    service = AuthService()
    result = service.update_own_profile(
        access_token="token",
        user_id="missing",
        first_name="A",
        last_name="B",
        whatsapp="",
        job_title="",
    )

    assert not result.success


def test_update_own_password_success(monkeypatch, fake_client: MagicMock) -> None:
    monkeypatch.setattr(
        "src.services.auth_service.get_supabase",
        lambda: fake_client,
    )

    service = AuthService()
    result = service.update_own_password(
        access_token="access-token",
        refresh_token="refresh-token",
        password="NovaSenha@2026",
    )

    assert result.success
    fake_client.auth.set_session.assert_called_once_with(
        "access-token", "refresh-token"
    )
    fake_client.auth.update_user.assert_called_once_with(
        {"password": "NovaSenha@2026"}
    )


def test_update_own_password_failure_is_reported(
    monkeypatch, fake_client: MagicMock
) -> None:
    monkeypatch.setattr(
        "src.services.auth_service.get_supabase",
        lambda: fake_client,
    )
    fake_client.auth.update_user.side_effect = RuntimeError("boom")

    service = AuthService()
    result = service.update_own_password(
        access_token="access-token",
        refresh_token="refresh-token",
        password="NovaSenha@2026",
    )

    assert not result.success
