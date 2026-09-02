from pathlib import Path
from typing import Any

from src.config.constants import ROLE_LABELS


def role_label(role: str | None) -> str:
    """Rótulo amigável do papel — nunca o termo técnico do enum."""
    return ROLE_LABELS.get(role or "", "Usuário")


def display_job_title(profile: dict[str, Any]) -> str:
    """Cargo do usuário para exibição. Cai para o rótulo do papel se vazio."""
    job_title = (profile.get("job_title") or "").strip()
    return job_title or role_label(profile.get("role"))


def resolve_avatar_path(profile: dict[str, Any]) -> str | None:
    """Caminho local da foto de perfil, só se o arquivo ainda existir em disco."""
    avatar_path = (profile.get("avatar_path") or "").strip()
    return avatar_path if avatar_path and Path(avatar_path).is_file() else None
