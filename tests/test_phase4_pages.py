"""Testes de aceite da Fase 4: painel do parceiro e painel administrativo
na página Início (pages/00)."""
from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.services.goal_service import GoalService, ServiceResult as GoalResult
from src.services.partner_service import PartnerService, ServiceResult as PartnerResult
from src.services.supporter_service import (
    ServiceResult as SupporterResult,
    SupporterService,
)

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
    "job_title": "Parceiro",
}

STAFF_PROFILE = {
    "id": "11111111-1111-1111-1111-111111111111",
    "first_name": "Ana",
    "last_name": "Admin",
    "email": "admin@exemplo.com",
    "role": "admin",
    "job_title": "Administração",
}


def test_partner_dashboard_shows_metrics(monkeypatch) -> None:
    monkeypatch.setattr(PartnerService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        PartnerService,
        "get_partner_for_profile",
        lambda self, profile_id: PartnerResult(
            success=True,
            message="ok",
            data={"id": PARTNER_PROFILE["id"], "public_slug": "padaria"},
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
                "target_count": 10,
                "achieved_count": 4,
                "status": "active",
            },
        ),
    )
    monkeypatch.setattr(
        GoalService,
        "list_recent",
        lambda self, partner_id: GoalResult(success=True, message="ok", data=[]),
    )

    monkeypatch.setattr(SupporterService, "__init__", lambda self, access_token=None: None)
    monkeypatch.setattr(
        SupporterService,
        "count_for_partner",
        lambda self, partner_id: SupporterResult(success=True, message="ok", data=4),
    )
    monkeypatch.setattr(
        SupporterService,
        "list_for_partner",
        lambda self, partner_id: SupporterResult(success=True, message="ok", data=[]),
    )

    at = AppTest.from_file(_page("00_🏠_Dashboard.py"))
    _login_as(at, PARTNER_PROFILE)
    at.run()

    assert not at.exception
    metric_values = [m.value for m in at.metric]
    assert "4" in metric_values
    assert "10" in metric_values


def test_partner_dashboard_warns_when_not_linked(monkeypatch) -> None:
    monkeypatch.setattr(PartnerService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        PartnerService,
        "get_partner_for_profile",
        lambda self, profile_id: PartnerResult(success=True, message="ok", data=None),
    )

    at = AppTest.from_file(_page("00_🏠_Dashboard.py"))
    _login_as(at, PARTNER_PROFILE)
    at.run()

    assert not at.exception
    assert any("não está vinculado" in w.value for w in at.warning)


def test_partner_dashboard_flags_duplicate_whatsapp(monkeypatch) -> None:
    monkeypatch.setattr(PartnerService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        PartnerService,
        "get_partner_for_profile",
        lambda self, profile_id: PartnerResult(
            success=True, message="ok", data={"id": "p1", "public_slug": "padaria"}
        ),
    )
    monkeypatch.setattr(GoalService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        GoalService,
        "get_goal",
        lambda self, partner_id, goal_date: GoalResult(success=True, message="ok", data=None),
    )
    monkeypatch.setattr(
        GoalService,
        "list_recent",
        lambda self, partner_id: GoalResult(success=True, message="ok", data=[]),
    )

    duplicated_supporters = [
        {
            "id": "s1",
            "first_name": "Ana",
            "last_name": "Silva",
            "whatsapp": "+5531999999999",
            "created_at": "2026-09-01T10:00:00Z",
        },
        {
            "id": "s2",
            "first_name": "Ana",
            "last_name": "Souza",
            "whatsapp": "+5531999999999",
            "created_at": "2026-09-02T10:00:00Z",
        },
    ]

    monkeypatch.setattr(SupporterService, "__init__", lambda self, access_token=None: None)
    monkeypatch.setattr(
        SupporterService,
        "count_for_partner",
        lambda self, partner_id: SupporterResult(success=True, message="ok", data=2),
    )
    monkeypatch.setattr(
        SupporterService,
        "list_for_partner",
        lambda self, partner_id: SupporterResult(
            success=True, message="ok", data=duplicated_supporters
        ),
    )

    at = AppTest.from_file(_page("00_🏠_Dashboard.py"))
    _login_as(at, PARTNER_PROFILE)
    at.run(timeout=15)

    assert not at.exception
    assert any("cadastro" in w.value.lower() for w in at.warning)


def test_staff_dashboard_shows_ranking_and_metrics(monkeypatch) -> None:
    monkeypatch.setattr(PartnerService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        PartnerService,
        "list_partners",
        lambda self: PartnerResult(
            success=True,
            message="ok",
            data=[
                {"id": "p1", "public_slug": "padaria", "is_accepting_supporters": True},
                {"id": "p2", "public_slug": "acougue", "is_accepting_supporters": False},
            ],
        ),
    )

    monkeypatch.setattr(GoalService, "__init__", lambda self, access_token: None)
    monkeypatch.setattr(
        GoalService,
        "list_today_for_staff",
        lambda self, goal_date: GoalResult(
            success=True,
            message="ok",
            data=[
                {
                    "partner_id": "p1",
                    "target_count": 10,
                    "achieved_count": 10,
                    "status": "achieved",
                    "partners": {
                        "public_slug": "padaria",
                        "profiles": {"first_name": "William", "last_name": "E"},
                    },
                },
                {
                    "partner_id": "p2",
                    "target_count": 5,
                    "achieved_count": 1,
                    "status": "active",
                    "partners": {
                        "public_slug": "acougue",
                        "profiles": {"first_name": "Bia", "last_name": "C"},
                    },
                },
            ],
        ),
    )

    monkeypatch.setattr(SupporterService, "__init__", lambda self, access_token=None: None)
    monkeypatch.setattr(
        SupporterService,
        "list_all_for_staff",
        lambda self: SupporterResult(success=True, message="ok", data=[]),
    )

    at = AppTest.from_file(_page("00_🏠_Dashboard.py"))
    _login_as(at, STAFF_PROFILE)
    at.run(timeout=15)

    assert not at.exception
    metric_values = [m.value for m in at.metric]
    assert "2" in metric_values  # total de parceiros
    assert "1" in metric_values  # parceiros ativos / metas atingidas hoje
