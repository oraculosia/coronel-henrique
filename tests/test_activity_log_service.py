from unittest.mock import MagicMock

from src.services.activity_log_service import log_activity


def test_log_activity_inserts_expected_payload() -> None:
    client = MagicMock()

    log_activity(
        client,
        actor_id="user-1",
        entity_type="partner",
        action="created",
        entity_id="partner-1",
        metadata={"public_slug": "padaria"},
    )

    client.table.assert_called_once_with("activity_logs")
    payload = client.table.return_value.insert.call_args.args[0]
    assert payload == {
        "actor_id": "user-1",
        "entity_type": "partner",
        "entity_id": "partner-1",
        "action": "created",
        "metadata": {"public_slug": "padaria"},
    }


def test_log_activity_defaults_metadata_to_empty_dict() -> None:
    client = MagicMock()

    log_activity(client, actor_id="user-1", entity_type="daily_goal", action="updated")

    payload = client.table.return_value.insert.call_args.args[0]
    assert payload["metadata"] == {}
    assert payload["entity_id"] is None


def test_log_activity_never_raises_on_failure() -> None:
    client = MagicMock()
    client.table.return_value.insert.return_value.execute.side_effect = RuntimeError(
        "boom"
    )

    log_activity(client, actor_id="user-1", entity_type="partner", action="created")
