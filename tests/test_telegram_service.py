from datetime import date
from unittest.mock import MagicMock

import pytest

from src.services.telegram_service import TelegramService


@pytest.fixture
def fake_admin_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(monkeypatch, fake_admin_client: MagicMock) -> TelegramService:
    monkeypatch.setattr(
        "src.services.telegram_service.get_supabase_admin",
        lambda: fake_admin_client,
    )
    monkeypatch.setattr(
        "src.services.telegram_service.settings.TELEGRAM_BOT_TOKEN", "bot-token"
    )
    monkeypatch.setattr(
        "src.services.telegram_service.settings.TELEGRAM_CHAT_ID", "123"
    )
    return TelegramService()


def _mock_partner_chat_lookup(fake_admin_client: MagicMock, chat_id) -> None:
    fake_admin_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"telegram_chat_id": chat_id}]
    )


def test_notify_new_supporter_uses_partner_chat_id(
    monkeypatch, service: TelegramService, fake_admin_client: MagicMock
) -> None:
    _mock_partner_chat_lookup(fake_admin_client, "999888")

    sent_calls = []

    class FakeResponse:
        status_code = 200

    def fake_post(url, json, timeout):
        sent_calls.append(json)
        return FakeResponse()

    monkeypatch.setattr("src.services.telegram_service.requests.post", fake_post)

    result = service.notify_new_supporter(
        partner_id="p1",
        partner_label="Padaria",
        supporter_id="s1",
        first_name="Ana",
        last_name="Silva",
    )

    assert result.success
    assert sent_calls[0]["chat_id"] == "999888"
    assert "Padaria" in sent_calls[0]["text"]


def test_notify_new_supporter_falls_back_to_default_chat(
    monkeypatch, service: TelegramService, fake_admin_client: MagicMock
) -> None:
    _mock_partner_chat_lookup(fake_admin_client, None)

    sent_calls = []
    monkeypatch.setattr(
        "src.services.telegram_service.requests.post",
        lambda url, json, timeout: sent_calls.append(json)
        or type("R", (), {"status_code": 200})(),
    )

    service.notify_new_supporter(
        partner_id="p1",
        partner_label="Padaria",
        supporter_id="s1",
        first_name="Ana",
        last_name="Silva",
    )

    assert sent_calls[0]["chat_id"] == "123"


def test_notify_goal_if_reached_skips_when_no_goal(
    service: TelegramService, fake_admin_client: MagicMock
) -> None:
    fake_admin_client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )

    result = service.notify_goal_if_reached(
        partner_id="p1", partner_label="Padaria", goal_date=date(2026, 9, 1)
    )

    assert result.success
    assert result.data == {"skipped": True}


def test_notify_goal_if_reached_skips_when_not_achieved(
    service: TelegramService, fake_admin_client: MagicMock
) -> None:
    fake_admin_client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"id": "g1", "status": "active", "notified_at": None, "target_count": 10}]
    )

    result = service.notify_goal_if_reached(
        partner_id="p1", partner_label="Padaria", goal_date=date(2026, 9, 1)
    )

    assert result.success
    assert result.data == {"skipped": True}


def test_notify_goal_if_reached_skips_when_already_notified(
    service: TelegramService, fake_admin_client: MagicMock
) -> None:
    fake_admin_client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[
            {
                "id": "g1",
                "status": "achieved",
                "notified_at": "2026-09-01T10:00:00+00:00",
                "target_count": 10,
            }
        ]
    )

    result = service.notify_goal_if_reached(
        partner_id="p1", partner_label="Padaria", goal_date=date(2026, 9, 1)
    )

    assert result.success
    assert result.data == {"skipped": True}


def test_notify_goal_if_reached_sends_and_claims_once(
    monkeypatch, service: TelegramService, fake_admin_client: MagicMock
) -> None:
    fake_admin_client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[
            {
                "id": "g1",
                "status": "achieved",
                "notified_at": None,
                "target_count": 10,
            }
        ]
    )
    fake_admin_client.table.return_value.update.return_value.eq.return_value.is_.return_value.execute.return_value = MagicMock(
        data=[{"id": "g1"}]
    )
    _mock_partner_chat_lookup(fake_admin_client, "999888")

    sent_calls = []
    monkeypatch.setattr(
        "src.services.telegram_service.requests.post",
        lambda url, json, timeout: sent_calls.append(json)
        or type("R", (), {"status_code": 200})(),
    )

    result = service.notify_goal_if_reached(
        partner_id="p1", partner_label="Padaria", goal_date=date(2026, 9, 1)
    )

    assert result.success
    assert len(sent_calls) == 1
    assert "10" in sent_calls[0]["text"]

    update_call = fake_admin_client.table.return_value.update.call_args.args[0]
    assert "notified_at" in update_call
    is_call_args = fake_admin_client.table.return_value.update.return_value.eq.return_value.is_.call_args.args
    assert is_call_args == ("notified_at", "null")


def test_notify_goal_if_reached_race_loses_claim(
    service: TelegramService, fake_admin_client: MagicMock
) -> None:
    fake_admin_client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[
            {
                "id": "g1",
                "status": "achieved",
                "notified_at": None,
                "target_count": 10,
            }
        ]
    )
    fake_admin_client.table.return_value.update.return_value.eq.return_value.is_.return_value.execute.return_value = MagicMock(
        data=[]
    )

    result = service.notify_goal_if_reached(
        partner_id="p1", partner_label="Padaria", goal_date=date(2026, 9, 1)
    )

    assert result.success
    assert result.data == {"skipped": True}
