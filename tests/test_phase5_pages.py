"""Testes de aceite da Fase 5 (Assistente IA): chat e base de conhecimento."""
from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.services.ai_service import AIService, ServiceResult as AIResult
from src.services.knowledge_service import KnowledgeService, ServiceResult as KnowledgeResult

ROOT_DIR = Path(__file__).resolve().parents[1]


def _page(name: str) -> str:
    return str(ROOT_DIR / "pages" / name)


def _login_as(at: AppTest, profile: dict) -> None:
    at.session_state["authenticated"] = True
    at.session_state["access_token"] = "access-token"
    at.session_state["refresh_token"] = "refresh-token"
    at.session_state["user_id"] = profile["id"]
    at.session_state["user_email"] = profile["email"]
    at.session_state["profile"] = profile


PARTNER_PROFILE = {
    "id": "22222222-2222-2222-2222-222222222222",
    "first_name": "William",
    "last_name": "Eustáquio",
    "email": "parceiro@exemplo.com",
    "role": "parceiro",
}

STAFF_PROFILE = {
    "id": "11111111-1111-1111-1111-111111111111",
    "first_name": "Ana",
    "last_name": "Admin",
    "email": "admin@exemplo.com",
    "role": "admin",
}

SUPER_ADMIN_PROFILE = {
    "id": "33333333-3333-3333-3333-333333333333",
    "first_name": "Rafael",
    "last_name": "Super",
    "email": "super@exemplo.com",
    "role": "super_admin",
}


def test_assistant_page_shows_history_and_answers_question(monkeypatch) -> None:
    monkeypatch.setattr(AIService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        AIService,
        "list_own_history",
        lambda self, user_id, limit=10: AIResult(success=True, message="ok", data=[]),
    )
    monkeypatch.setattr(
        AIService,
        "ask",
        lambda self, user_id, role, question: AIResult(
            success=True,
            message="ok",
            data={"answer": "A campanha funciona assim...", "sources": [{"id": "d1", "title": "Doc"}]},
        ),
    )

    at = AppTest.from_file(_page("01_🤖_Assistente_IA.py"))
    _login_as(at, PARTNER_PROFILE)
    at.run()

    assert not at.exception
    at.chat_input[0].set_value("Como funciona a campanha?").run()

    assert not at.exception
    all_text = [msg.value for msg in at.markdown] + [msg.value for msg in at.text]
    assert any("campanha funciona" in value for value in all_text)


def test_assistant_page_shows_error_when_ai_disabled(monkeypatch) -> None:
    monkeypatch.setattr(AIService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        AIService,
        "list_own_history",
        lambda self, user_id, limit=10: AIResult(success=True, message="ok", data=[]),
    )
    monkeypatch.setattr(
        AIService,
        "ask",
        lambda self, user_id, role, question: AIResult(
            success=False, message="Assistente IA não configurado."
        ),
    )

    at = AppTest.from_file(_page("01_🤖_Assistente_IA.py"))
    _login_as(at, PARTNER_PROFILE)
    at.run()
    at.chat_input[0].set_value("Oi").run()

    assert not at.exception
    assert any("não configurado" in e.value for e in at.error)


def test_knowledge_page_blocks_non_staff() -> None:
    at = AppTest.from_file(_page("10_📚_Base_de_Conhecimento.py"))
    _login_as(at, PARTNER_PROFILE)
    at.run()

    assert any(e.value for e in at.error)


def test_knowledge_page_blocks_admin() -> None:
    at = AppTest.from_file(_page("10_📚_Base_de_Conhecimento.py"))
    _login_as(at, STAFF_PROFILE)
    at.run()

    assert any(e.value for e in at.error)


def test_knowledge_page_lists_documents_for_staff(monkeypatch) -> None:
    monkeypatch.setattr(KnowledgeService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        KnowledgeService,
        "list_all_for_staff",
        lambda self: KnowledgeResult(
            success=True,
            message="ok",
            data=[
                {
                    "id": "d1",
                    "title": "Sobre a campanha",
                    "content": "Texto explicativo",
                    "audience_roles": ["parceiro"],
                    "is_active": True,
                }
            ],
        ),
    )

    monkeypatch.setattr(AIService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        AIService,
        "list_all_history",
        lambda self, limit=100: AIResult(success=True, message="ok", data=[]),
    )

    at = AppTest.from_file(_page("10_📚_Base_de_Conhecimento.py"))
    _login_as(at, SUPER_ADMIN_PROFILE)
    at.run()

    assert not at.exception
    assert any("Sobre a campanha" in e.label for e in at.expander)


# ---------------------------------------------------------------------------
# Assistente IA público (sem login)
# ---------------------------------------------------------------------------


def test_public_chat_page_answers_question(monkeypatch) -> None:
    monkeypatch.setattr(AIService, "__init__", lambda self, access_token=None: None)
    monkeypatch.setattr(
        AIService,
        "ask_public",
        lambda self, question: AIResult(
            success=True, message="ok", data={"answer": "Os projetos incluem..."}
        ),
    )

    at = AppTest.from_file(_page("11_💬_Fale_com_a_Campanha.py"))
    at.run()

    assert not at.exception
    at.chat_input[0].set_value("Quais os projetos do Coronel Henrique?").run()

    assert not at.exception
    all_text = [msg.value for msg in at.markdown] + [msg.value for msg in at.text]
    assert any("projetos incluem" in value for value in all_text)


def test_public_chat_page_shows_supporter_button(monkeypatch) -> None:
    monkeypatch.setattr(AIService, "__init__", lambda self, access_token=None: None)

    at = AppTest.from_file(_page("11_💬_Fale_com_a_Campanha.py"))
    at.run()

    assert not at.exception
    assert any("Quero ser apoiador" in b.label for b in at.button)
