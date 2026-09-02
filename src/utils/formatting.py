from typing import Any

from src.config.constants import ROLE_LABELS


def role_label(role: str | None) -> str:
    """Rótulo amigável do papel — nunca o termo técnico do enum."""
    return ROLE_LABELS.get(role or "", "Usuário")


def display_job_title(profile: dict[str, Any]) -> str:
    """Cargo do usuário para exibição. Cai para o rótulo do papel se vazio."""
    job_title = (profile.get("job_title") or "").strip()
    return job_title or role_label(profile.get("role"))
