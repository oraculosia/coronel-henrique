from unittest.mock import MagicMock

import pytest

from src.config.settings import settings
from src.services.ai_service import AIService, DEFAULT_GROQ_MODEL


@pytest.fixture
def fake_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(monkeypatch, fake_client: MagicMock) -> AIService:
    monkeypatch.setattr("src.services.ai_service.get_supabase", lambda: fake_client)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "fake-key")
    monkeypatch.setattr(settings, "GROQ_MODEL", "")
    return AIService(access_token="token")


def _isolate_tables(
    fake_client: MagicMock, target_table: str, target_mock: MagicMock
) -> None:
    other_table = MagicMock()

    def table_side_effect(name: str) -> MagicMock:
        if name == target_table:
            return target_mock
        return other_table

    fake_client.table.side_effect = table_side_effect


def _fake_groq(monkeypatch, answer: str = "Resposta gerada.") -> MagicMock:
    fake_completion = MagicMock()
    fake_completion.choices = [MagicMock(message=MagicMock(content=answer))]

    fake_groq_client = MagicMock()
    fake_groq_client.chat.completions.create.return_value = fake_completion

    fake_groq_class = MagicMock(return_value=fake_groq_client)
    monkeypatch.setattr("groq.Groq", fake_groq_class)
    return fake_groq_client


def test_ask_returns_error_when_api_key_missing(
    monkeypatch, service: AIService
) -> None:
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    result = service.ask(user_id="u1", role="parceiro", question="Como funciona?")

    assert not result.success
    assert "não configurado" in result.message.lower()


def test_ask_returns_error_when_question_is_empty(service: AIService) -> None:
    result = service.ask(user_id="u1", role="parceiro", question="   ")

    assert not result.success


def test_ask_success_returns_answer_and_saves_conversation(
    monkeypatch, service: AIService, fake_client: MagicMock
) -> None:
    knowledge_table = MagicMock()
    knowledge_table.select.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"id": "d1", "title": "Sobre a campanha", "content": "Texto"}]
    )
    conversations_table = MagicMock()

    def table_side_effect(name: str) -> MagicMock:
        if name == "knowledge_documents":
            return knowledge_table
        if name == "ai_conversations":
            return conversations_table
        raise AssertionError(f"unexpected table: {name}")

    fake_client.table.side_effect = table_side_effect

    fake_groq_client = _fake_groq(monkeypatch, answer="A campanha é...")

    result = service.ask(user_id="u1", role="parceiro", question="Como funciona?")

    assert result.success
    assert result.data["answer"] == "A campanha é..."
    assert result.data["sources"] == [{"id": "d1", "title": "Sobre a campanha"}]

    fake_groq_client.chat.completions.create.assert_called_once()
    call_kwargs = fake_groq_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == DEFAULT_GROQ_MODEL

    conversations_table.insert.assert_called_once()
    payload = conversations_table.insert.call_args.args[0]
    assert payload["user_id"] == "u1"
    assert payload["role"] == "parceiro"
    assert payload["question"] == "Como funciona?"
    assert payload["answer"] == "A campanha é..."


def test_ask_handles_groq_exception_gracefully(
    monkeypatch, service: AIService, fake_client: MagicMock
) -> None:
    fake_client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )

    fake_groq_client = MagicMock()
    fake_groq_client.chat.completions.create.side_effect = RuntimeError("boom")
    monkeypatch.setattr("groq.Groq", MagicMock(return_value=fake_groq_client))

    result = service.ask(user_id="u1", role="parceiro", question="Como funciona?")

    assert not result.success


def test_list_own_history_returns_rows(
    service: AIService, fake_client: MagicMock
) -> None:
    row = {"id": "c1", "question": "Q", "answer": "A", "sources": [], "created_at": "now"}
    fake_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[row]
    )

    result = service.list_own_history(user_id="u1")

    assert result.success
    assert result.data == [row]


def test_list_all_history_returns_rows(
    service: AIService, fake_client: MagicMock
) -> None:
    row = {
        "id": "c1",
        "question": "Q",
        "answer": "A",
        "role": "parceiro",
        "created_at": "now",
        "profiles": {"first_name": "William", "last_name": "E"},
    }
    fake_client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[row]
    )

    result = service.list_all_history()

    assert result.success
    assert result.data == [row]
