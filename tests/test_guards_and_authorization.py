from src.auth import authorization, guards
from src.auth.session import initialize_session, set_authenticated_session


def _profile(role: str) -> dict:
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "email": "user@exemplo.com",
        "role": role,
    }


def test_current_role_none_when_not_authenticated() -> None:
    initialize_session()
    assert authorization.current_role() is None


def test_current_role_returns_profile_role() -> None:
    initialize_session()
    set_authenticated_session(
        access_token="t",
        refresh_token="r",
        profile=_profile("parceiro"),
    )
    assert authorization.current_role() == "parceiro"


def test_has_role_matches_any_given_role() -> None:
    initialize_session()
    set_authenticated_session(
        access_token="t",
        refresh_token="r",
        profile=_profile("admin"),
    )
    assert authorization.has_role("admin", "super_admin") is True
    assert authorization.has_role("parceiro") is False


def test_is_super_admin() -> None:
    initialize_session()
    set_authenticated_session(
        access_token="t",
        refresh_token="r",
        profile=_profile("super_admin"),
    )
    assert authorization.is_super_admin() is True
    assert authorization.is_admin_or_super_admin() is True
    assert authorization.is_partner() is False


def test_is_partner() -> None:
    initialize_session()
    set_authenticated_session(
        access_token="t",
        refresh_token="r",
        profile=_profile("parceiro"),
    )
    assert authorization.is_partner() is True
    assert authorization.is_super_admin() is False


def test_require_authentication_redirects_when_not_logged_in(monkeypatch) -> None:
    initialize_session()

    warnings: list[str] = []
    switches: list[str] = []
    monkeypatch.setattr(guards.st, "warning", lambda msg: warnings.append(msg))
    monkeypatch.setattr(guards.st, "switch_page", lambda page: switches.append(page))

    guards.require_authentication()

    assert switches == ["pages/05_🔐_Login.py"]
    assert warnings


def test_require_authentication_allows_logged_in_user(monkeypatch) -> None:
    initialize_session()
    set_authenticated_session(
        access_token="t",
        refresh_token="r",
        profile=_profile("apoiador"),
    )

    switches: list[str] = []
    monkeypatch.setattr(guards.st, "switch_page", lambda page: switches.append(page))

    guards.require_authentication()

    assert switches == []


def test_require_roles_blocks_wrong_role(monkeypatch) -> None:
    initialize_session()
    set_authenticated_session(
        access_token="t",
        refresh_token="r",
        profile=_profile("apoiador"),
    )

    errors: list[str] = []
    stops: list[bool] = []
    monkeypatch.setattr(guards.st, "error", lambda msg: errors.append(msg))
    monkeypatch.setattr(guards.st, "stop", lambda: stops.append(True))

    guards.require_roles("super_admin", "admin")

    assert errors
    assert stops == [True]


def test_require_roles_allows_matching_role(monkeypatch) -> None:
    initialize_session()
    set_authenticated_session(
        access_token="t",
        refresh_token="r",
        profile=_profile("super_admin"),
    )

    errors: list[str] = []
    stops: list[bool] = []
    monkeypatch.setattr(guards.st, "error", lambda msg: errors.append(msg))
    monkeypatch.setattr(guards.st, "stop", lambda: stops.append(True))

    guards.require_roles("super_admin", "admin")

    assert errors == []
    assert stops == []
