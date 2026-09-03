from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.config.constants import GOAL_STATUS_LABELS, ROLE_LABELS


def role_label(role: str | None) -> str:
    """Rótulo amigável do papel — nunca o termo técnico do enum."""
    return ROLE_LABELS.get(role or "", "Usuário")


def goal_status_label(status: str | None) -> str:
    """Rótulo amigável do status de meta — nunca o termo técnico do enum."""
    return GOAL_STATUS_LABELS.get(status or "", status or "—")


def format_date_br(value: str | date | datetime | None) -> str:
    """Formata uma data (sem hora) no padrão brasileiro dd/mm/aaaa."""
    if not value:
        return "—"
    if isinstance(value, str):
        value = date.fromisoformat(value[:10])
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%d/%m/%Y")


def format_datetime_br(value: str | datetime | None) -> str:
    """Formata data e hora no padrão brasileiro dd/mm/aaaa HH:MM:SS."""
    if not value:
        return "—"
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.strftime("%d/%m/%Y %H:%M:%S")


def display_job_title(profile: dict[str, Any]) -> str:
    """Cargo do usuário para exibição. Cai para o rótulo do papel se vazio."""
    job_title = (profile.get("job_title") or "").strip()
    return job_title or role_label(profile.get("role"))


def resolve_avatar_path(profile: dict[str, Any]) -> str | None:
    """Caminho local da foto de perfil, só se o arquivo ainda existir em disco."""
    avatar_path = (profile.get("avatar_path") or "").strip()
    return avatar_path if avatar_path and Path(avatar_path).is_file() else None
