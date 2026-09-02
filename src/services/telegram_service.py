from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

import requests

from src.config.settings import settings
from src.database.supabase_client import get_supabase_admin


@dataclass
class ServiceResult:
    success: bool
    message: str
    data: Any = None


class TelegramService:
    """Envio de alertas Telegram usando o schema real (sem tabela própria
    de idempotência):

    - Novo apoiador: enviado uma vez por chamada, logo após o INSERT
      (1:1 com o cadastro; não existe supporters.notified_at).
    - Meta atingida: idempotência via daily_goals.notified_at — a
      atualização condicional (`is_("notified_at", "null")`) garante que
      só quem "ganha" a corrida efetivamente envia a mensagem.

    Usa sempre o client de service role (bypassa RLS): tanto para ler
    telegram_chat_id de partners quanto para reivindicar notified_at.
    """

    def __init__(self) -> None:
        self.admin_client = get_supabase_admin()
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.default_chat_id = settings.TELEGRAM_CHAT_ID

    def _resolve_chat_id(self, partner_id: str) -> str:
        response = (
            self.admin_client.table("partners")
            .select("telegram_chat_id")
            .eq("id", partner_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        partner_chat_id = rows[0].get("telegram_chat_id") if rows else None
        return partner_chat_id or self.default_chat_id

    def _send(self, chat_id: str, text: str) -> ServiceResult:
        if not self.bot_token or not chat_id:
            return ServiceResult(
                success=False, message="Telegram não configurado (.env)."
            )

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
        except Exception:
            return ServiceResult(
                success=False, message="Falha de rede ao enviar Telegram."
            )

        if response.status_code != 200:
            return ServiceResult(
                success=False,
                message=f"Telegram respondeu {response.status_code}.",
            )

        return ServiceResult(success=True, message="Notificação enviada.")

    def notify_new_supporter(
        self,
        partner_id: str,
        partner_label: str,
        supporter_id: str,
        first_name: str,
        last_name: str,
    ) -> ServiceResult:
        chat_id = self._resolve_chat_id(partner_id)
        text = (
            f"🙌 Novo apoiador em <b>{partner_label}</b>: "
            f"{first_name} {last_name}".strip()
        )
        return self._send(chat_id, text)

    def notify_goal_if_reached(
        self,
        partner_id: str,
        partner_label: str,
        goal_date: date | None = None,
    ) -> ServiceResult:
        target_date = (goal_date or date.today()).isoformat()

        rows = (
            self.admin_client.table("daily_goals")
            .select("id, status, notified_at, target_count")
            .eq("partner_id", partner_id)
            .eq("goal_date", target_date)
            .limit(1)
            .execute()
            .data
            or []
        )

        if not rows:
            return ServiceResult(
                success=True,
                message="Sem meta definida para este dia.",
                data={"skipped": True},
            )

        goal = rows[0]

        if goal["status"] != "achieved" or goal.get("notified_at"):
            return ServiceResult(
                success=True, message="Nada a notificar.", data={"skipped": True}
            )

        claim = (
            self.admin_client.table("daily_goals")
            .update({"notified_at": datetime.now(timezone.utc).isoformat()})
            .eq("id", goal["id"])
            .is_("notified_at", "null")
            .execute()
        )

        if not claim.data:
            return ServiceResult(
                success=True,
                message="Meta já havia sido notificada.",
                data={"skipped": True},
            )

        chat_id = self._resolve_chat_id(partner_id)
        text = (
            f"🎯 Meta atingida! <b>{partner_label}</b> alcançou "
            f"{goal['target_count']} cadastros em {target_date}."
        )
        return self._send(chat_id, text)
