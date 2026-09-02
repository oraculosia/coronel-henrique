from collections import defaultdict
from datetime import datetime, timedelta, timezone
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
        "access_token": None,
        "refresh_token": None,
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


def test_send_verification_code_success(service: AuthService, monkeypatch) -> None:
    admin = MagicMock()
    monkeypatch.setattr("src.services.auth_service.get_supabase_admin", lambda: admin)
    notificador = MagicMock()
    monkeypatch.setattr("src.services.auth_service.Notificador", lambda: notificador)

    result = service.send_verification_code(
        user_id="user-1", email="a@b.com", first_name="Ana"
    )

    assert result.success
    admin.table.return_value.delete.return_value.eq.assert_called_once_with(
        "user_id", "user-1"
    )
    notificador.enviar_codigo_verificacao.assert_called_once()
    _, kwargs = notificador.enviar_codigo_verificacao.call_args
    assert kwargs["destino"] == "a@b.com"
    assert len(kwargs["codigo"]) == 6


def _fake_admin_with_tables(monkeypatch) -> "defaultdict[str, MagicMock]":
    tables: "defaultdict[str, MagicMock]" = defaultdict(MagicMock)

    admin = MagicMock()
    admin.table.side_effect = lambda name: tables[name]
    monkeypatch.setattr("src.services.auth_service.get_supabase_admin", lambda: admin)

    return tables


def test_verify_own_code_success(service: AuthService, monkeypatch) -> None:
    tables = _fake_admin_with_tables(monkeypatch)

    tables["profiles"].select.return_value.eq.return_value.single.return_value.execute.return_value = (
        SimpleNamespace(data={"id": "user-1"})
    )

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    tables[
        "email_verification_codes"
    ].select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = SimpleNamespace(
        data=[
            {
                "id": "code-1",
                "code_hash": AuthService._hash_code("123456"),
                "expires_at": expires_at,
                "consumed_at": None,
            }
        ]
    )

    result = service.verify_own_code(email="a@b.com", code="123456")

    assert result.success
    assert result.data == {"user_id": "user-1", "email": "a@b.com"}
    tables["email_verification_codes"].update.assert_called_once()
    tables["profiles"].update.assert_called_once_with(
        {"verification_status": "verified"}
    )


def test_verify_own_code_creates_partner_link(service: AuthService, monkeypatch) -> None:
    tables = _fake_admin_with_tables(monkeypatch)

    tables["profiles"].select.return_value.eq.return_value.single.return_value.execute.return_value = (
        SimpleNamespace(data={"id": "user-1", "first_name": "Homem", "last_name": "Aranha"})
    )

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    tables[
        "email_verification_codes"
    ].select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = SimpleNamespace(
        data=[
            {
                "id": "code-1",
                "code_hash": AuthService._hash_code("123456"),
                "expires_at": expires_at,
                "consumed_at": None,
            }
        ]
    )
    # Nenhum vínculo em partners ainda, e o slug candidato está livre.
    tables[
        "partners"
    ].select.return_value.eq.return_value.limit.return_value.execute.return_value = (
        SimpleNamespace(data=[])
    )

    result = service.verify_own_code(email="a@b.com", code="123456")

    assert result.success
    tables["partners"].insert.assert_called_once_with(
        {
            "id": "user-1",
            "public_slug": "homem-aranha",
            "is_accepting_supporters": True,
            "created_by": "user-1",
        }
    )


def test_verify_own_code_wrong_code(service: AuthService, monkeypatch) -> None:
    tables = _fake_admin_with_tables(monkeypatch)
    tables["profiles"].select.return_value.eq.return_value.single.return_value.execute.return_value = (
        SimpleNamespace(data={"id": "user-1"})
    )

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    tables[
        "email_verification_codes"
    ].select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = SimpleNamespace(
        data=[
            {
                "id": "code-1",
                "code_hash": AuthService._hash_code("123456"),
                "expires_at": expires_at,
                "consumed_at": None,
            }
        ]
    )

    result = service.verify_own_code(email="a@b.com", code="000000")

    assert not result.success


def test_verify_own_code_expired(service: AuthService, monkeypatch) -> None:
    tables = _fake_admin_with_tables(monkeypatch)

    tables["profiles"].select.return_value.eq.return_value.single.return_value.execute.return_value = (
        SimpleNamespace(data={"id": "user-1"})
    )

    expires_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    tables[
        "email_verification_codes"
    ].select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = SimpleNamespace(
        data=[
            {
                "id": "code-1",
                "code_hash": AuthService._hash_code("123456"),
                "expires_at": expires_at,
                "consumed_at": None,
            }
        ]
    )

    result = service.verify_own_code(email="a@b.com", code="123456")

    assert not result.success
    assert "expirado" in result.message.lower()


def test_resend_own_code_success(service: AuthService, monkeypatch) -> None:
    tables = _fake_admin_with_tables(monkeypatch)
    notificador = MagicMock()
    monkeypatch.setattr("src.services.auth_service.Notificador", lambda: notificador)

    tables["profiles"].select.return_value.eq.return_value.single.return_value.execute.return_value = (
        SimpleNamespace(
            data={"id": "user-1", "first_name": "Ana", "verification_status": "pending"}
        )
    )

    result = service.resend_own_code(email="a@b.com")

    assert result.success
    notificador.enviar_codigo_verificacao.assert_called_once()


def test_resend_own_code_already_verified(service: AuthService, monkeypatch) -> None:
    tables = _fake_admin_with_tables(monkeypatch)

    tables["profiles"].select.return_value.eq.return_value.single.return_value.execute.return_value = (
        SimpleNamespace(
            data={
                "id": "user-1",
                "first_name": "Ana",
                "verification_status": "verified",
            }
        )
    )

    result = service.resend_own_code(email="a@b.com")

    assert not result.success
    assert "já está confirmado" in result.message


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
