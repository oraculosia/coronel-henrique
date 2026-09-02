from unittest.mock import MagicMock

import pytest

from src.services.supporter_service import SupporterService, find_duplicate_whatsapp


@pytest.fixture
def fake_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(monkeypatch, fake_client: MagicMock) -> SupporterService:
    monkeypatch.setattr(
        "src.services.supporter_service.get_supabase", lambda: fake_client
    )
    return SupporterService()


def test_resolve_partner_by_slug_found(
    service: SupporterService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[
            {
                "id": "p1",
                "public_slug": "padaria",
                "campaign_message": "Padaria do João",
                "is_accepting_supporters": True,
            }
        ]
    )

    result = service.resolve_partner_by_slug("padaria")

    assert result.success
    assert result.data["campaign_message"] == "Padaria do João"


def test_resolve_partner_by_slug_not_found(
    service: SupporterService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )

    result = service.resolve_partner_by_slug("inexistente")

    assert not result.success
    assert "não encontrado" in result.message.lower()


def test_register_public_requires_consent(service: SupporterService) -> None:
    result = service.register_public(
        partner_id="p1",
        slug="padaria",
        first_name="Ana",
        last_name="Silva",
        whatsapp="+5531999999999",
        consent_lgpd=False,
    )

    assert not result.success
    assert "lgpd" in result.message.lower()


def test_register_public_success_sets_consent_and_defaults(
    service: SupporterService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "s1", "first_name": "Ana"}]
    )

    result = service.register_public(
        partner_id="p1",
        slug="padaria",
        first_name="Ana",
        last_name="Silva",
        whatsapp="+5531999999999",
        consent_lgpd=True,
    )

    assert result.success
    assert result.data["id"] == "s1"
    payload = fake_client.table.return_value.insert.call_args.args[0]
    assert payload["partner_id"] == "p1"
    assert payload["source_slug"] == "padaria"
    assert payload["consent_lgpd"] is True
    assert payload["consent_at"] is not None
    assert payload["is_valid"] is True
    assert payload["source_utm"] == {}


def test_register_public_insert_failure(
    service: SupporterService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.insert.return_value.execute.side_effect = (
        RuntimeError("new row violates row-level security policy")
    )

    result = service.register_public(
        partner_id="p1",
        slug="padaria",
        first_name="Ana",
        last_name="Silva",
        whatsapp="+5531999999999",
        consent_lgpd=True,
    )

    assert not result.success


def test_list_for_partner_returns_rows(
    service: SupporterService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
        data=[{"first_name": "Ana"}]
    )

    result = service.list_for_partner(partner_id="p1")

    assert result.success
    assert result.data == [{"first_name": "Ana"}]


def test_count_for_partner_returns_count(
    service: SupporterService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"id": "s1"}], count=7
    )

    result = service.count_for_partner(partner_id="p1")

    assert result.success
    assert result.data == 7
    select_kwargs = fake_client.table.return_value.select.call_args.kwargs
    assert select_kwargs.get("count") == "exact"


def test_count_for_partner_defaults_to_zero_on_none(
    service: SupporterService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[], count=None
    )

    result = service.count_for_partner(partner_id="p1")

    assert result.success
    assert result.data == 0


def test_list_all_for_staff_returns_rows_with_partner_info(
    service: SupporterService, fake_client: MagicMock
) -> None:
    row = {
        "first_name": "Ana",
        "last_name": "Silva",
        "whatsapp": "+5531999999999",
        "partners": {"public_slug": "padaria", "profiles": {"first_name": "William"}},
    }
    fake_client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
        data=[row]
    )

    result = service.list_all_for_staff()

    assert result.success
    assert result.data == [row]


def test_find_duplicate_whatsapp_groups_repeated_numbers() -> None:
    supporters = [
        {"first_name": "Ana", "last_name": "Silva", "whatsapp": "+5531999999999"},
        {"first_name": "Ana", "last_name": "Souza", "whatsapp": "+5531999999999"},
        {"first_name": "Bia", "last_name": "Costa", "whatsapp": "+5531988888888"},
    ]

    duplicates = find_duplicate_whatsapp(supporters)

    assert len(duplicates) == 1
    assert duplicates[0]["whatsapp"] == "+5531999999999"
    assert duplicates[0]["count"] == 2


def test_find_duplicate_whatsapp_ignores_missing_whatsapp() -> None:
    supporters = [
        {"first_name": "Ana", "last_name": "Silva", "whatsapp": None},
        {"first_name": "Bia", "last_name": "Costa", "whatsapp": None},
    ]

    assert find_duplicate_whatsapp(supporters) == []


def test_find_duplicate_whatsapp_no_duplicates_returns_empty() -> None:
    supporters = [
        {"first_name": "Ana", "last_name": "Silva", "whatsapp": "+5531999999999"},
        {"first_name": "Bia", "last_name": "Costa", "whatsapp": "+5531988888888"},
    ]

    assert find_duplicate_whatsapp(supporters) == []
