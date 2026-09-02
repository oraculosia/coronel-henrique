from unittest.mock import MagicMock

import pytest

from src.services.knowledge_service import KnowledgeService


@pytest.fixture
def fake_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(monkeypatch, fake_client: MagicMock) -> KnowledgeService:
    monkeypatch.setattr(
        "src.services.knowledge_service.get_supabase", lambda: fake_client
    )
    return KnowledgeService(access_token="token")


def _isolate_tables(fake_client: MagicMock, target_table: str, target_mock: MagicMock) -> None:
    activity_logs_table = MagicMock()

    def table_side_effect(name: str) -> MagicMock:
        if name == target_table:
            return target_mock
        if name == "activity_logs":
            return activity_logs_table
        raise AssertionError(f"unexpected table: {name}")

    fake_client.table.side_effect = table_side_effect


def test_list_for_role_returns_rows(
    service: KnowledgeService, fake_client: MagicMock
) -> None:
    row = {"id": "d1", "title": "Sobre a campanha", "content": "...", "audience_roles": ["parceiro"]}
    fake_client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[row]
    )

    result = service.list_for_role()

    assert result.success
    assert result.data == [row]


def test_list_all_for_staff_returns_rows(
    service: KnowledgeService, fake_client: MagicMock
) -> None:
    row = {
        "id": "d1",
        "title": "Sobre a campanha",
        "content": "...",
        "audience_roles": ["parceiro"],
        "is_active": True,
    }
    fake_client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
        data=[row]
    )

    result = service.list_all_for_staff()

    assert result.success
    assert result.data == [row]


def test_create_document_success(
    service: KnowledgeService, fake_client: MagicMock
) -> None:
    documents_table = MagicMock()
    documents_table.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "d1", "title": "Sobre a campanha"}]
    )
    _isolate_tables(fake_client, "knowledge_documents", documents_table)

    result = service.create_document(
        title="Sobre a campanha",
        content="Texto explicativo.",
        audience_roles=["parceiro", "admin"],
        created_by="user-1",
    )

    assert result.success
    assert result.data == {"id": "d1", "title": "Sobre a campanha"}
    payload = documents_table.insert.call_args.args[0]
    assert payload["title"] == "Sobre a campanha"
    assert payload["audience_roles"] == ["parceiro", "admin"]
    assert payload["created_by"] == "user-1"


def test_create_document_failure_returns_error(
    service: KnowledgeService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.insert.return_value.execute.side_effect = RuntimeError(
        "boom"
    )

    result = service.create_document(
        title="X", content="Y", audience_roles=["parceiro"], created_by="user-1"
    )

    assert not result.success


def test_update_document_only_sends_provided_fields(
    service: KnowledgeService, fake_client: MagicMock
) -> None:
    documents_table = MagicMock()
    _isolate_tables(fake_client, "knowledge_documents", documents_table)

    result = service.update_document(
        document_id="d1", actor_id="user-1", is_active=False
    )

    assert result.success
    payload = documents_table.update.call_args.args[0]
    assert payload == {"updated_by": "user-1", "is_active": False}


def test_update_document_failure_returns_error(
    service: KnowledgeService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.update.return_value.eq.return_value.execute.side_effect = RuntimeError(
        "boom"
    )

    result = service.update_document(document_id="d1", actor_id="user-1", title="Novo")

    assert not result.success
