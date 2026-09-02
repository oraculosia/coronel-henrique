from datetime import date
from unittest.mock import MagicMock

import pytest

from src.services.goal_service import GoalService


@pytest.fixture
def fake_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(monkeypatch, fake_client: MagicMock) -> GoalService:
    monkeypatch.setattr("src.services.goal_service.get_supabase", lambda: fake_client)
    return GoalService(access_token="token")


def test_get_goal_returns_none_when_not_created(
    service: GoalService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )

    result = service.get_goal(partner_id="p1", goal_date=date(2026, 9, 1))

    assert result.success
    assert result.data is None


def test_get_goal_returns_existing_row(
    service: GoalService, fake_client: MagicMock
) -> None:
    row = {
        "id": "g1",
        "target_count": 10,
        "achieved_count": 3,
        "status": "active",
        "notified_at": None,
    }
    fake_client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[row]
    )

    result = service.get_goal(partner_id="p1", goal_date=date(2026, 9, 1))

    assert result.success
    assert result.data == row


def test_create_goal_success(service: GoalService, fake_client: MagicMock) -> None:
    goals_table = MagicMock()
    goals_table.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "g1", "target_count": 10}]
    )
    activity_logs_table = MagicMock()

    def table_side_effect(name: str) -> MagicMock:
        return activity_logs_table if name == "activity_logs" else goals_table

    fake_client.table.side_effect = table_side_effect

    result = service.create_goal(
        partner_id="p1",
        goal_date=date(2026, 9, 1),
        target_count=10,
        created_by="p1",
    )

    assert result.success
    assert result.data["target_count"] == 10
    insert_payload = goals_table.insert.call_args.args[0]
    assert insert_payload["created_by"] == "p1"

    log_payload = activity_logs_table.insert.call_args.args[0]
    assert log_payload["entity_type"] == "daily_goal"
    assert log_payload["action"] == "created"
    assert log_payload["actor_id"] == "p1"


def test_create_goal_duplicate_returns_friendly_message(
    service: GoalService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.insert.return_value.execute.side_effect = (
        RuntimeError(
            "duplicate key value violates unique constraint "
            "\"daily_goals_unique_partner_date\""
        )
    )

    result = service.create_goal(
        partner_id="p1",
        goal_date=date(2026, 9, 1),
        target_count=10,
        created_by="p1",
    )

    assert not result.success
    assert "já existe" in result.message.lower()


def test_update_target_success(service: GoalService, fake_client: MagicMock) -> None:
    fake_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "g1", "target_count": 20}]
    )

    result = service.update_target(goal_id="g1", target_count=20, actor_id="p1")

    assert result.success
    assert result.data["target_count"] == 20
    update_payload = fake_client.table.return_value.update.call_args.args[0]
    assert update_payload == {"target_count": 20}


def test_update_target_failure_when_no_rows(
    service: GoalService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )

    result = service.update_target(goal_id="g1", target_count=20, actor_id="p1")

    assert not result.success


def test_list_recent_returns_rows(service: GoalService, fake_client: MagicMock) -> None:
    fake_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"goal_date": "2026-09-01", "status": "achieved"}]
    )

    result = service.list_recent(partner_id="p1")

    assert result.success
    assert result.data == [{"goal_date": "2026-09-01", "status": "achieved"}]


def test_list_today_for_staff_returns_rows_ordered_by_achieved(
    service: GoalService, fake_client: MagicMock
) -> None:
    row = {
        "partner_id": "p1",
        "target_count": 10,
        "achieved_count": 4,
        "status": "active",
        "partners": {"public_slug": "padaria", "profiles": {"first_name": "William"}},
    }
    fake_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
        data=[row]
    )

    result = service.list_today_for_staff(goal_date=date(2026, 9, 2))

    assert result.success
    assert result.data == [row]
