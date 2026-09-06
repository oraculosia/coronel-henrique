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
    1. Notificação para o Parceiro (com dados completos do apoiador cadastrado em seu link).
    2. Notificação para o Admin (gestão com total acumulado e dados do cadastro).
    3. Alertas de meta diária atingida e progresso.
    4. Resumo diário e alertas de sistema.
    """

    def __init__(self) -> None:
        self.admin_client = get_supabase_admin()
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.default_chat_id = settings.TELEGRAM_CHAT_ID
        self.tz_br = zoneinfo.ZoneInfo("America/Sao_Paulo")

    def _get_now_br(self) -> datetime:
        """Retorna o datetime atual no fuso horário brasileiro."""
        return datetime.now(self.tz_br)

    def _resolve_partner_info(self, partner_id: str) -> tuple[str, str | None]:
        """Busca o nome e o telegram_chat_id específico do parceiro."""
        partner_chat_id = None
        partner_name = "Campanha Oficial"

        try:
            # Busca telegram_chat_id na tabela partners
            p_res = (
                self.admin_client.table("partners")
                .select("telegram_chat_id")
                .eq("id", partner_id)
                .limit(1)
                .execute()
            )
            if p_res.data:
                partner_chat_id = p_res.data[0].get("telegram_chat_id")

            # Busca nome do parceiro em profiles
            prof_res = (
                self.admin_client.table("profiles")
                .select("first_name, last_name")
                .eq("id", partner_id)
                .limit(1)
                .execute()
            )
            if prof_res.data:
                first = prof_res.data[0].get("first_name", "")
                last = prof_res.data[0].get("last_name", "")
                name = f"{first} {last}".strip()
                if name:
                    partner_name = name

        except Exception:
            pass

        return partner_name, partner_chat_id

    def _get_partner_supporter_count(self, partner_id: str) -> int:
        """Retorna o total de apoiadores já cadastrados por este parceiro."""
        try:
            res = (
                self.admin_client.table("supporters")
                .select("id", count="exact")
                .eq("partner_id", partner_id)
                .execute()
            )
            return res.count or 0
        except Exception:
            return 0

    def _get_global_supporter_count(self) -> int:
        """Retorna o total geral de apoiadores em toda a campanha."""
        try:
            res = (
                self.admin_client.table("supporters")
                .select("id", count="exact")
                .execute()
            )
            return res.count or 0
        except Exception:
            return 0

    def _send(self, chat_id: str, text: str) -> ServiceResult:
        """Executa a requisição HTTP para a API do Telegram."""
        if not self.bot_token or not chat_id:
            return ServiceResult(
                success=False,
                message="Telegram não configurado (.env ou chat_id ausente).",
            )

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
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
        email: str = "",
        created_at: datetime | str | None = None,
    ) -> ServiceResult:
        """Dispara notificações simultâneas para o ADMIN e para o PARCEIRO responsável.

        1. Para o Admin: Gestão com total acumulado da campanha e do parceiro.
        2. Para o Parceiro: Dados completos do apoiador que usou seu link.
        """
        # 1. Trata data e formatação
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

        # 2. Resolve informações e contagens
        resolved_name, partner_chat_id = self._resolve_partner_info(partner_id)
        partner_display = partner_label or resolved_name
        full_name = f"{first_name or ''} {last_name or ''}".strip() or "Não informado"
        phone_display = phone.strip() if phone else "Não informado"
        email_display = email.strip() if email else "Não informado"

        partner_total = self._get_partner_supporter_count(partner_id)
        global_total = self._get_global_supporter_count()

        admin_sent = False
        partner_sent = False

        # ---------------------------------------------------------------------
        # 3. MENSAGEM PARA O ADMIN (Visão de Gestão Global)
        # ---------------------------------------------------------------------
        if self.default_chat_id:
            text_admin = (
                f"🔔 <b>NOVO APOIADOR CADASTRADO (PAINEL GERAL)</b>\n\n"
                f"👤 <b>Apoiador:</b> {html.escape(full_name)}\n"
                f"📱 <b>WhatsApp:</b> {html.escape(phone_display)}\n"
                f"📧 <b>E-mail:</b> {html.escape(email_display)}\n"
                f"🏢 <b>Parceiro Indicador:</b> {html.escape(partner_display)}\n"
                f"🗓 <b>Data e Hora:</b> {html.escape(formatted_date)}\n\n"
                f"📊 <b>MÉTRICAS DE CAMPANHA:</b>\n"
                f"• Cadastros deste Parceiro: <b>{partner_total}</b>\n"
                f"• Total Geral da Campanha: <b>{global_total}</b>"
            )
            admin_res = self._send(self.default_chat_id, text_admin)
            admin_sent = admin_res.success

        # ---------------------------------------------------------------------
        # 4. MENSAGEM PARA O PARCEIRO (Seus Apoiadores Diretos)
        # ---------------------------------------------------------------------
        # Se o parceiro tiver telegram_chat_id próprio e for diferente do admin geral
        if partner_chat_id and str(partner_chat_id) != str(self.default_chat_id):
            text_partner = (
                f"🎉 <b>PARABÉNS! NOVO APOIADOR PELO SEU LINK!</b>\n\n"
                f"Olá, <b>{html.escape(partner_display)}</b>! Mais um apoiador acabou de se cadastrar através da sua referência:\n\n"
                f"👤 <b>Nome:</b> {html.escape(full_name)}\n"
                f"📱 <b>WhatsApp:</b> {html.escape(phone_display)}\n"
                f"📧 <b>E-mail:</b> {html.escape(email_display)}\n"
                f"🗓 <b>Data:</b> {html.escape(formatted_date)}\n\n"
                f"🎯 <b>Seu total de indicados até agora:</b> {partner_total} apoiadores\n\n"
                f"<i>Continue compartilhando seu link e multiplicando nossa voz por Minas Gerais! 🇧🇷🚀</i>"
            )
            partner_res = self._send(partner_chat_id, text_partner)
            partner_sent = partner_res.success
        else:
            partner_sent = True  # Ignora se não configurou chat individual

        return ServiceResult(
            success=admin_sent or partner_sent,
            message="Notificações processadas.",
            data={"admin_sent": admin_sent, "partner_sent": partner_sent},
        )

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
            .select("id, status, notified_at, target_count, achieved_count")
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

        resolved_name, partner_chat_id = self._resolve_partner_info(partner_id)
        display_name = partner_label or resolved_name
        now_time = self._get_now_br().strftime("%H:%M")
        formatted_date = target_date_obj.strftime("%d/%m/%Y")

        text = (
            f"🎯 <b>META DIÁRIA ATINGIDA COM SUCESSO!</b>\n\n"
            f"🏢 <b>Parceiro:</b> {html.escape(display_name)}\n"
            f"📈 <b>Objetivo batido:</b> {goal['target_count']} apoiadores\n"
            f"🗓 <b>Data:</b> {formatted_date} às {now_time}\n\n"
            f"🚀 <b>Parabéns pelo trabalho e engajamento na campanha!</b>"
        )

        # Envia para o admin e também para o chat do parceiro (se houver)
        self._send(self.default_chat_id, text)
        if partner_chat_id and str(partner_chat_id) != str(self.default_chat_id):
            self._send(partner_chat_id, text)

        return ServiceResult(success=True, message="Notificação de meta enviada.")

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
            f"🤝 <b>NOVO PARCEIRO CADASTRADO NO SISTEMA!</b>\n\n"
            f"🏢 <b>Nome / Liderança:</b> {html.escape(partner_name)}\n"
            f"📧 <b>E-mail:</b> {html.escape(email or 'Não informado')}\n"
            f"📱 <b>WhatsApp:</b> {html.escape(phone or 'Não informado')}\n"
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
                ranking_lines += f"{idx}º {name} — {count} cadastros\n"

        text = (
            f"📊 <b>RESUMO DIÁRIO DE CADASTROS (ADMIN)</b>\n"
            f"🗓 <b>Data:</b> {formatted_date}\n\n"
            f"👥 <b>Total de novos apoiadores hoje:</b> {total_supporters}\n"
            f"🏢 <b>Parceiros ativos hoje:</b> {active_partners_count}"
            f"{ranking_lines}\n"
            f"⚙️ <i>Relatório consolidado gerado automaticamente pela plataforma.</i>"
        )

        return self._send(dest_chat_id, text)
