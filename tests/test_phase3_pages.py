"""Testes de aceite da Fase 3 (schema real): parceiros, metas, apoiadores e
cadastro público."""
from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.services.goal_service import GoalService
from src.services.partner_service import PartnerService
from src.services.supporter_service import SupporterService
from src.services.telegram_service import TelegramService

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


def _partner_profile() -> dict:
    return {
        "id": "22222222-2222-2222-2222-222222222222",
        "first_name": "William",
        "last_name": "Eustáquio",
        "email": "parceiro@exemplo.com",
        "role": "parceiro",
    }


PARTNER_RECORD = {
    "id": "22222222-2222-2222-2222-222222222222",
    "public_slug": "padaria",
    "campaign_message": "Padaria do João",
    "telegram_chat_id": None,
    "is_accepting_supporters": True,
}


# ---------------------------------------------------------------------------
# Parceiros (admin/super_admin)
# ---------------------------------------------------------------------------


def test_partners_page_lists_existing_partners(monkeypatch, verified_profile) -> None:
    from src.services.partner_service import ServiceResult as PartnerResult

    monkeypatch.setattr(PartnerService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        PartnerService,
        "list_unlinked_partner_profiles",
        lambda self: PartnerResult(success=True, message="ok", data=[]),
    )
    monkeypatch.setattr(
        PartnerService,
        "list_partners",
        lambda self: PartnerResult(
            success=True,
            message="ok",
            data=[
                {
                    **PARTNER_RECORD,
                    "profiles": {
                        "first_name": "William",
                        "last_name": "Eustáquio",
                        "email": "programador.descpro@gmail.com",
                    },
                }
            ],
        ),
    )

    at = AppTest.from_file(_page("04_🤝_Parceiros.py"))
    _login_as(at, verified_profile)
    at.run()

    assert not at.exception
    assert any("William" in md.value for md in at.markdown)


def test_partners_page_blocks_non_admin(monkeypatch) -> None:
    at = AppTest.from_file(_page("04_🤝_Parceiros.py"))
    _login_as(at, _partner_profile())
    at.run()

    assert any(e.value for e in at.error)


# ---------------------------------------------------------------------------
# Metas
# ---------------------------------------------------------------------------


def test_goals_page_offers_to_create_goal_when_missing(monkeypatch) -> None:
    from src.services.partner_service import ServiceResult as PartnerResult
    from src.services.goal_service import ServiceResult as GoalResult

    monkeypatch.setattr(PartnerService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        PartnerService,
        "get_partner_for_profile",
        lambda self, profile_id: PartnerResult(
            success=True, message="ok", data=PARTNER_RECORD
        ),
    )

    monkeypatch.setattr(GoalService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        GoalService,
        "get_goal",
        lambda self, partner_id, goal_date: GoalResult(success=True, message="ok", data=None),
    )

    at = AppTest.from_file(_page("03_🎯_Metas.py"))
    _login_as(at, _partner_profile())
    at.run()

    assert not at.exception
    assert any("não existe meta criada" in i.value for i in at.info)


def test_goals_page_shows_today_metrics_and_notifies_when_achieved(monkeypatch) -> None:
    from src.services.partner_service import ServiceResult as PartnerResult
    from src.services.goal_service import ServiceResult as GoalResult

    monkeypatch.setattr(PartnerService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        PartnerService,
        "get_partner_for_profile",
        lambda self, profile_id: PartnerResult(
            success=True, message="ok", data=PARTNER_RECORD
        ),
    )

    monkeypatch.setattr(GoalService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        GoalService,
        "get_goal",
        lambda self, partner_id, goal_date: GoalResult(
            success=True,
            message="ok",
            data={
                "id": "g1",
                "target_count": 10,
                "achieved_count": 10,
                "status": "achieved",
                "notified_at": None,
            },
        ),
    )
    monkeypatch.setattr(
        GoalService,
        "list_recent",
        lambda self, partner_id: GoalResult(success=True, message="ok", data=[]),
    )

    notify_calls = []
    monkeypatch.setattr(TelegramService, "__init__", lambda self: None)
    monkeypatch.setattr(
        TelegramService,
        "notify_goal_if_reached",
        lambda self, **kwargs: notify_calls.append(kwargs)
        or __import__(
            "src.services.telegram_service", fromlist=["ServiceResult"]
        ).ServiceResult(success=True, message="ok", data={"skipped": False}),
    )

    at = AppTest.from_file(_page("03_🎯_Metas.py"))
    _login_as(at, _partner_profile())
    at.run()

    assert not at.exception
    metric_values = [m.value for m in at.metric]
    assert "10" in metric_values
    assert len(notify_calls) == 1
    assert notify_calls[0]["partner_id"] == PARTNER_RECORD["id"]


def test_goals_page_warns_when_partner_not_linked(monkeypatch) -> None:
    from src.services.partner_service import ServiceResult as PartnerResult

    monkeypatch.setattr(PartnerService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        PartnerService,
        "get_partner_for_profile",
        lambda self, profile_id: PartnerResult(success=True, message="ok", data=None),
    )

    at = AppTest.from_file(_page("03_🎯_Metas.py"))
    _login_as(at, _partner_profile())
    at.run()

    assert any("não está vinculado" in w.value for w in at.warning)


# ---------------------------------------------------------------------------
# Apoiadores
# ---------------------------------------------------------------------------


def test_supporters_page_lists_supporters_for_partner(monkeypatch) -> None:
    from src.services.partner_service import ServiceResult as PartnerResult
    from src.services.supporter_service import ServiceResult as SupporterResult

    monkeypatch.setattr(PartnerService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        PartnerService,
        "get_partner_for_profile",
        lambda self, profile_id: PartnerResult(
            success=True, message="ok", data=PARTNER_RECORD
        ),
    )

    monkeypatch.setattr(SupporterService, "__init__", lambda self, access_token=None: None)
    monkeypatch.setattr(
        SupporterService,
        "list_for_partner",
        lambda self, partner_id: SupporterResult(
            success=True,
            message="ok",
            data=[
                {
                    "first_name": "Ana",
                    "last_name": "Silva",
                    "whatsapp": "+5531999999999",
                    "is_valid": True,
                    "created_at": "2026-09-01T10:00:00Z",
                }
            ],
        ),
    )

    at = AppTest.from_file(_page("02_👥_Apoiadores.py"))
    _login_as(at, _partner_profile())
    # primeira renderizacao de st.dataframe pode importar pyarrow a frio
    at.run(timeout=15)

    assert not at.exception
    assert any(m.value == "1" for m in at.metric)


# ---------------------------------------------------------------------------
# Cadastro público de apoiador
# ---------------------------------------------------------------------------


def test_public_signup_missing_slug_warns() -> None:
    at = AppTest.from_file(_page("09_🙌_Cadastro_Apoiador.py"))
    at.run()

    assert any("Link inválido" in w.value for w in at.warning)


def test_public_signup_unknown_slug_shows_error(monkeypatch) -> None:
    from src.services.supporter_service import ServiceResult

    monkeypatch.setattr(SupporterService, "__init__", lambda self, access_token=None: None)
    monkeypatch.setattr(
        SupporterService,
        "resolve_partner_by_slug",
        lambda self, slug: ServiceResult(
            success=False, message="Link de parceiro não encontrado ou inativo."
        ),
    )

    at = AppTest.from_file(_page("09_🙌_Cadastro_Apoiador.py"))
    at.query_params["p"] = "inexistente"
    at.run()

    assert any("não encontrado" in e.value for e in at.error)


def test_public_signup_requires_whatsapp_and_consent(monkeypatch) -> None:
    from src.services.supporter_service import ServiceResult

    monkeypatch.setattr(SupporterService, "__init__", lambda self, access_token=None: None)
    monkeypatch.setattr(
        SupporterService,
        "resolve_partner_by_slug",
        lambda self, slug: ServiceResult(
            success=True, message="ok", data=dict(PARTNER_RECORD)
        ),
    )

    at = AppTest.from_file(_page("09_🙌_Cadastro_Apoiador.py"))
    at.query_params["p"] = "padaria"
    at.run()

    at.text_input[0].input("Ana")
    at.text_input[1].input("Silva")
    # whatsapp fica vazio, checkbox de consentimento não é marcado
    at.button[0].click()
    at.run()

    errors = [e.value for e in at.error]
    assert any("consentimento" in e.lower() or "lgpd" in e.lower() for e in errors)


def test_public_signup_success_notifies_telegram(monkeypatch) -> None:
    from src.services.supporter_service import ServiceResult as SupporterResult

    monkeypatch.setattr(SupporterService, "__init__", lambda self, access_token=None: None)
    monkeypatch.setattr(
        SupporterService,
        "resolve_partner_by_slug",
        lambda self, slug: SupporterResult(
            success=True, message="ok", data=dict(PARTNER_RECORD)
        ),
    )
    monkeypatch.setattr(
        SupporterService,
        "register_public",
        lambda self, **kwargs: SupporterResult(
            success=True,
            message="Cadastro realizado com sucesso!",
            data={"id": "s1", "first_name": "Ana"},
        ),
    )

    notified = {}
    monkeypatch.setattr(TelegramService, "__init__", lambda self: None)
    monkeypatch.setattr(
        TelegramService,
        "notify_new_supporter",
        lambda self, **kwargs: notified.setdefault("new_supporter", kwargs),
    )
    monkeypatch.setattr(
        TelegramService,
        "notify_goal_if_reached",
        lambda self, **kwargs: notified.setdefault("goal_reached", kwargs),
    )

    at = AppTest.from_file(_page("09_🙌_Cadastro_Apoiador.py"))
    at.query_params["p"] = "padaria"
    at.run()

    at.text_input[0].input("Ana")
    at.text_input[1].input("Silva")
    at.text_input[2].input("31999999999")
    at.checkbox[0].check()
    at.button[0].click()
    at.run()

    assert not at.exception
    assert any("sucesso" in s.value.lower() for s in at.success)
    assert notified["new_supporter"]["supporter_id"] == "s1"
    assert notified["goal_reached"]["partner_id"] == PARTNER_RECORD["id"]
