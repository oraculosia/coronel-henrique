from unittest.mock import MagicMock

import pytest

from src.services.partner_service import PartnerService


@pytest.fixture
def fake_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(monkeypatch, fake_client: MagicMock) -> PartnerService:
    monkeypatch.setattr(
        "src.services.partner_service.get_supabase", lambda: fake_client
    )
    return PartnerService(access_token="token")


def test_service_authenticates_postgrest_with_token(
    service: PartnerService, fake_client: MagicMock
) -> None:
    fake_client.postgrest.auth.assert_called_once_with("token")


def test_list_partners_returns_rows(service: PartnerService, fake_client: MagicMock) -> None:
    fake_client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
        data=[{"id": "profile-1", "public_slug": "padaria"}]
    )

    result = service.list_partners()

    assert result.success
    assert result.data == [{"id": "profile-1", "public_slug": "padaria"}]


def test_list_unlinked_partner_profiles_excludes_linked(
    service: PartnerService, fake_client: MagicMock
) -> None:
    profiles_execute = MagicMock(
        data=[
            {"id": "u1", "first_name": "Ana", "last_name": "Silva", "email": "a@b.com"},
            {"id": "u2", "first_name": "Bia", "last_name": "Souza", "email": "b@b.com"},
        ]
    )
    partners_execute = MagicMock(data=[{"id": "u2"}])

    def table_side_effect(name: str) -> MagicMock:
        table_mock = MagicMock()
        if name == "profiles":
            table_mock.select.return_value.eq.return_value.execute.return_value = (
                profiles_execute
            )
        elif name == "partners":
            table_mock.select.return_value.execute.return_value = partners_execute
        return table_mock

    fake_client.table.side_effect = table_side_effect

    result = service.list_unlinked_partner_profiles()

    assert result.success
    assert [p["id"] for p in result.data] == ["u1"]


def test_generate_unique_slug_returns_base_when_available(
    service: PartnerService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )

    slug = service.generate_unique_slug("Padaria do João")

    assert slug == "padaria-do-joao"


def test_generate_unique_slug_appends_suffix_on_conflict(
    service: PartnerService, fake_client: MagicMock
) -> None:
    execute_mock = (
        fake_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute
    )
    execute_mock.side_effect = [
        MagicMock(data=[{"id": "existing"}]),
        MagicMock(data=[]),
    ]

    slug = service.generate_unique_slug("Padaria")

    assert slug == "padaria-2"


def test_create_partner_uses_profile_id_as_partner_id(
    service: PartnerService, fake_client: MagicMock
) -> None:
    partners_table = MagicMock()
    partners_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )
    partners_table.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "profile-1", "public_slug": "padaria"}]
    )
    activity_logs_table = MagicMock()

    def table_side_effect(name: str) -> MagicMock:
        return activity_logs_table if name == "activity_logs" else partners_table

    fake_client.table.side_effect = table_side_effect

    result = service.create_partner(
        profile_id="profile-1",
        created_by="admin-1",
        slug_seed="Padaria",
    )

    assert result.success
    assert result.data["id"] == "profile-1"
    insert_payload = partners_table.insert.call_args.args[0]
    assert insert_payload["id"] == "profile-1"
    assert insert_payload["created_by"] == "admin-1"
    assert insert_payload["is_accepting_supporters"] is True

    log_payload = activity_logs_table.insert.call_args.args[0]
    assert log_payload["entity_type"] == "partner"
    assert log_payload["action"] == "created"
    assert log_payload["actor_id"] == "admin-1"


def test_create_partner_duplicate_slug_returns_friendly_message(
    service: PartnerService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )
    fake_client.table.return_value.insert.return_value.execute.side_effect = (
        RuntimeError("duplicate key value violates unique constraint partners_public_slug_key")
    )

    result = service.create_partner(
        profile_id="profile-1", created_by="admin-1", slug_seed="Padaria"
    )

    assert not result.success
    assert "link" in result.message.lower()


def test_update_partner_no_fields_is_noop(service: PartnerService) -> None:
    result = service.update_partner(partner_id="p1", actor_id="admin-1")
    assert result.success
    assert result.message == "Nada para atualizar."


def test_update_partner_success(service: PartnerService, fake_client: MagicMock) -> None:
    fake_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "p1", "is_accepting_supporters": False}]
    )

    result = service.update_partner(
        partner_id="p1", actor_id="admin-1", is_accepting_supporters=False
    )

    assert result.success
    assert result.data["is_accepting_supporters"] is False


def test_get_partner_for_profile_returns_none_when_absent(
    service: PartnerService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )

    result = service.get_partner_for_profile(profile_id="profile-1")

    assert result.success
    assert result.data is None
