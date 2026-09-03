import html
import zoneinfo
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
    """Envio e gerenciamento de notificações profissionais via Telegram.

    Suporta:
    - Notificação de novo apoiador (direcionada ao admin).
    - Meta diária atingida (com idempotência via Supabase).
    - Alerta de aproximação de meta (ex: 80% atingido).
    - Boas-vindas/ativação de novos parceiros (para o admin).
    - Resumo diário de performance (admin ou canal geral).
    - Alertas de erros críticos / falhas de integração.
    """

    def __init__(self) -> None:
        self.admin_client = get_supabase_admin()
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.default_chat_id = settings.TELEGRAM_CHAT_ID
        self.tz_br = zoneinfo.ZoneInfo("America/Sao_Paulo")

    def _get_now_br(self) -> datetime:
        """Retorna o datetime atual no fuso horário brasileiro."""
        return datetime.now(self.tz_br)

    def _resolve_chat_id(self, partner_id: str) -> str:
        """Busca o chat_id específico do parceiro ou usa o default."""
        try:
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
        except Exception:
            return self.default_chat_id

    def _send(self, chat_id: str, text: str) -> ServiceResult:
        """Executa a requisição HTTP para a API do Telegram."""
        if not self.bot_token or not chat_id:
            return ServiceResult(
                success=False,
                message="Telegram não configurado (.env ausente ou incompleto).",
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
        except Exception as exc:
            return ServiceResult(
                success=False,
                message=f"Falha de rede ao conectar com Telegram: {exc}",
            )

        if response.status_code != 200:
            return ServiceResult(
                success=False,
                message=f"Telegram respondeu com status {response.status_code}: {response.text}",
            )

        return ServiceResult(success=True, message="Notificação enviada com sucesso.")

    def notify_new_supporter(
        self,
        partner_id: str,
        partner_label: str,
        supporter_id: str,
        first_name: str,
        last_name: str,
        phone: str = "",
        created_at: datetime | str | None = None,
    ) -> ServiceResult:
        """Notifica o admin sobre o cadastro de um novo apoiador."""
        if isinstance(created_at, datetime):
            dt_br = created_at.astimezone(self.tz_br) if created_at.tzinfo else created_at.replace(tzinfo=self.tz_br)
            formatted_date = dt_br.strftime("%d/%m/%Y às %H:%M")
        elif isinstance(created_at, str) and created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                dt_br = dt.astimezone(self.tz_br)
                formatted_date = dt_br.strftime("%d/%m/%Y às %H:%M")
            except Exception:
                formatted_date = created_at
        else:
            formatted_date = self._get_now_br().strftime("%d/%m/%Y às %H:%M")

        full_name = f"{first_name or ''} {last_name or ''}".strip() or "Não informado"
        phone_display = phone.strip() if phone else "Não informado"

        text = (
            f"🙌 <b>Novo apoiador cadastrado por {html.escape(partner_label)}:</b>\n\n"
            f"👤 <b>Nome:</b> {html.escape(full_name)}\n"
            f"📱 <b>WhatsApp:</b> {html.escape(phone_display)}\n"
            f"🗓 <b>Data e hora:</b> {html.escape(formatted_date)}"
        )

        return self._send(self.default_chat_id, text)

    def notify_goal_if_reached(
        self,
        partner_id: str,
        partner_label: str,
        goal_date: date | None = None,
    ) -> ServiceResult:
        """Alerta de meta atingida com proteção contra disparos duplicados."""
        target_date_obj = goal_date or date.today()
        target_date = target_date_obj.isoformat()

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
        now_time = self._get_now_br().strftime("%H:%M")
        formatted_date = target_date_obj.strftime("%d/%m/%Y")

        text = (
            f"🎯 <b>Meta Diária Atingida!</b>\n\n"
            f"🏢 <b>Parceiro:</b> {html.escape(partner_label)}\n"
            f"📈 <b>Objetivo batido:</b> {goal['target_count']} cadastros\n"
            f"🗓 <b>Data:</b> {formatted_date}\n"
            f"⏰ <b>Horário:</b> {now_time}\n\n"
            f"🚀 <i>Parabéns à equipe pelo excelente resultado!</i>"
        )
        return self._send(chat_id, text)

    def notify_goal_progress(
        self,
        partner_id: str,
        partner_label: str,
        current_count: int,
        target_count: int,
    ) -> ServiceResult:
        """Notifica o parceiro quando ele atinge marcos parciais da meta (ex: 80%)."""
        if target_count <= 0:
            return ServiceResult(success=True, message="Meta inválida para cálculo.")

        percentage = int((current_count / target_count) * 100)
        remaining = max(target_count - current_count, 0)
        chat_id = self._resolve_chat_id(partner_id)

        text = (
            f"⚡ <b>Reta Final da Meta!</b>\n\n"
            f"🏢 <b>Parceiro:</b> {html.escape(partner_label)}\n"
            f"📊 <b>Progresso:</b> {percentage}% ({current_count}/{target_count})\n"
            f"🔥 <b>Faltam apenas:</b> {remaining} apoiadores\n\n"
            f"<i>Falta pouco para bater a meta de hoje, continue acelerando!</i>"
        )
        return self._send(chat_id, text)

    def notify_new_partner_onboarded(
        self,
        partner_name: str,
        email: str = "",
        phone: str = "",
        city: str = "",
    ) -> ServiceResult:
        """Notifica o admin sobre o cadastro ou ativação de um novo parceiro."""
        now_str = self._get_now_br().strftime("%d/%m/%Y às %H:%M")
        
        text = (
            f"🤝 <b>Novo Parceiro Cadastrado!</b>\n\n"
            f"🏢 <b>Nome / Entidade:</b> {html.escape(partner_name)}\n"
            f"📧 <b>E-mail:</b> {html.escape(email or 'Não informado')}\n"
            f"📱 <b>Telefone:</b> {html.escape(phone or 'Não informado')}\n"
            f"📍 <b>Cidade / Região:</b> {html.escape(city or 'Não informado')}\n"
            f"🗓 <b>Data de ingresso:</b> {now_str}"
        )
        return self._send(self.default_chat_id, text)

    def notify_daily_summary(
        self,
        summary_date: date | None,
        total_supporters: int,
        active_partners_count: int,
        top_partners: list[dict[str, Any]] | None = None,
        chat_id: str | None = None,
    ) -> ServiceResult:
        """Envia o resumo consolidado de captação diária para o admin."""
        target_date_obj = summary_date or date.today()
        formatted_date = target_date_obj.strftime("%d/%m/%Y")
        dest_chat_id = chat_id or self.default_chat_id

        ranking_lines = ""
        if top_partners:
            ranking_lines = "\n\n🏆 <b>Destaques do dia:</b>\n"
            for idx, partner in enumerate(top_partners, start=1):
                name = html.escape(str(partner.get("name", "Parceiro")))
                count = partner.get("count", 0)
                ranking_lines += f"{idx}º {name} — <b>{count}</b> cadastros\n"

        text = (
            f"📊 <b>Resumo Diário de Captação</b>\n"
            f"🗓 <b>Data de referência:</b> {formatted_date}\n\n"
            f"👥 <b>Total de novos apoiadores:</b> {total_supporters}\n"
            f"🏢 <b>Parceiros ativos hoje:</b> {active_partners_count}"
            f"{ranking_lines}\n"
            f"⚙️ <i>Relatório gerado automaticamente pelo sistema.</i>"
        )
        return self._send(dest_chat_id, text)

    def notify_system_error(
        self,
        service_name: str,
        error_message: str,
        details: str = "",
    ) -> ServiceResult:
        """Alerta imediato de erros críticos de integração ou webhooks para o admin."""
        now_str = self._get_now_br().strftime("%d/%m/%Y às %H:%M:%S")

        details_block = ""
        if details:
            details_block = f"\n🔍 <b>Detalhes técnicos:</b>\n<code>{html.escape(details[:300])}</code>\n"

        text = (
            f"🚨 <b>Alerta de Falha no Sistema</b>\n\n"
            f"🛠 <b>Módulo / Serviço:</b> {html.escape(service_name)}\n"
            f"⚠️ <b>Erro:</b> {html.escape(error_message)}\n"
            f"⏰ <b>Ocorrência:</b> {now_str}"
            f"{details_block}\n"
            f"<i>Verifique os logs da aplicação para mais informações.</i>"
        )
        return self._send(self.default_chat_id, text)
