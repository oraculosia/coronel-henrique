from src.auth.session import get_profile


def current_role() -> str | None:
    profile = get_profile()

    if not profile:
        return None

    return profile.get("role")


def has_role(*roles: str) -> bool:
    return current_role() in roles


def is_super_admin() -> bool:
    return has_role("super_admin")


def is_admin_or_super_admin() -> bool:
    return has_role("admin", "super_admin")


def is_partner() -> bool:
    return has_role("parceiro")