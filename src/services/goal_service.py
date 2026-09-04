from dataclasses import dataclass
from datetime import date
from typing import Any

from src.database.supabase_client import get_supabase
from src.services.activity_log_service import log_activity


@dataclass
class ServiceResult:
    success: bool
    message: str
    data: Any = None


class GoalService:
    """Criação/edição de metas diárias (target_count/achieved_count/status).

    achieved_count e status são geridos pelo trigger
    trg_increment_partner_daily_goal — este service só cria a linha do dia
    e edita target_count.
    """

    def __init__(self, access_token: str) -> None:
        self.client = get_supabase()
        self.client.postgrest.auth(access_token)

    def get_goal(self, partner_id: str, goal_date: date) -> ServiceResult:
        try:
            response = (
                self.client.table("daily_goals")
                .select(
                    "id, partner_id, goal_date, target_count, achieved_count, "
                    "status, notified_at"
                )
                .eq("partner_id", partner_id)
                .eq("goal_date", goal_date.isoformat())
                .limit(1)
                .execute()
            )
            rows = response.data or []
            return ServiceResult(
                success=True, message="ok", data=rows[0] if rows else None
            )
        except Exception:
            return ServiceResult(
                success=False, message="Não foi possível carregar a meta do dia."
            )

    def create_goal(
        self,
        partner_id: str,
        goal_date: date,
        target_count: int,
        created_by: str,
    ) -> ServiceResult:
        try:
            response = (
                self.client.table("daily_goals")
                .insert(
                    {
                        "partner_id": partner_id,
                        "goal_date": goal_date.isoformat(),
                        "target_count": target_count,
                        "created_by": created_by,
                    }
                )
                .execute()
            )
            if not response.data:
                return ServiceResult(
                    success=False, message="Não foi possível criar a meta."
                )

            log_activity(
                self.client,
                actor_id=created_by,
                entity_type="daily_goal",
                action="created",
                entity_id=response.data[0]["id"],
                metadata={"partner_id": partner_id, "target_count": target_count},
            )

            return ServiceResult(
                success=True, message="Meta criada.", data=response.data[0]
            )
        except Exception as error:
            message = str(error).lower()
            if "duplicate key" in message or "daily_goals_unique_partner_date" in message:
                return ServiceResult(
                    success=False,
                    message="Já existe uma meta criada para este dia. Edite-a abaixo.",
                )
            return ServiceResult(
                success=False, message="Não foi possível criar a meta."
            )

    def update_target(
        self, goal_id: str, target_count: int, actor_id: str
    ) -> ServiceResult:
        try:
            response = (
                self.client.table("daily_goals")
                .update({"target_count": target_count})
                .eq("id", goal_id)
                .execute()
            )
            if not response.data:
                return ServiceResult(
                    success=False, message="Não foi possível salvar a meta."
                )

            log_activity(
                self.client,
                actor_id=actor_id,
                entity_type="daily_goal",
                action="updated",
                entity_id=goal_id,
                metadata={"target_count": target_count},
            )

            return ServiceResult(
                success=True, message="Meta atualizada.", data=response.data[0]
            )
        except Exception:
            return ServiceResult(
                success=False, message="Não foi possível salvar a meta."
            )

    def list_recent(self, partner_id: str, limit: int = 14) -> ServiceResult:
        try:
            response = (
                self.client.table("daily_goals")
                .select(
                    "id, goal_date, target_count, achieved_count, status"
                )
                .eq("partner_id", partner_id)
                .order("goal_date", desc=True)
                .limit(limit)
                .execute()
            )
            return ServiceResult(success=True, message="ok", data=response.data or [])
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível carregar o histórico.",
                data=[],
            )

    def list_today_for_staff(self, goal_date: date) -> ServiceResult:
        """Metas de todos os parceiros num dia. Só admin/super_admin
        (policy daily_goals_staff_manage)."""
        try:
            response = (
                self.client.table("daily_goals")
                .select(
                    "id, partner_id, target_count, achieved_count, status, "
                    "partners(public_slug, profiles!partners_id_fkey(first_name, last_name))"
                )
                .eq("goal_date", goal_date.isoformat())
                .order("achieved_count", desc=True)
                .execute()
            )
            return ServiceResult(success=True, message="ok", data=response.data or [])
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível carregar as metas do dia.",
                data=[],
            )

    def list_range_for_staff(self, start_date: date, end_date: date) -> ServiceResult:
        """Metas de todos os parceiros num intervalo de datas (relatório
        semanal). Só admin/super_admin (policy daily_goals_staff_manage)."""
        try:
            response = (
                self.client.table("daily_goals")
                .select(
                    "id, partner_id, goal_date, target_count, achieved_count, "
                    "status, partners(public_slug, profiles!partners_id_fkey(first_name, last_name))"
                )
                .gte("goal_date", start_date.isoformat())
                .lte("goal_date", end_date.isoformat())
                .order("goal_date", desc=True)
                .execute()
            )
            return ServiceResult(success=True, message="ok", data=response.data or [])
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível carregar as metas do período.",
                data=[],
            )
