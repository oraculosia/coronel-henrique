from dataclasses import dataclass
from typing import Any

from slugify import slugify

from src.database.supabase_client import get_supabase
from src.services.activity_log_service import log_activity


@dataclass
class ServiceResult:
    success: bool
    message: str
    data: Any = None


class PartnerService:
    """Gestão de parceiros. partners.id é o MESMO id do profile do parceiro.

    Só admin/super_admin cria/edita (policy partners_staff_manage).
    """

    def __init__(self, access_token: str) -> None:
        self.client = get_supabase()
        self.client.postgrest.auth(access_token)

    def list_partners(self) -> ServiceResult:
        try:
            response = (
                self.client.table("partners")
                .select(
                    "id, public_slug, campaign_message, telegram_chat_id, "
                    "is_accepting_supporters, created_at, "
                    "profiles!id(first_name, last_name, email)"
                )
                .order("created_at", desc=True)
                .execute()
            )
            return ServiceResult(success=True, message="ok", data=response.data or [])
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível carregar os parceiros.",
                data=[],
            )

    def get_partner_for_profile(self, profile_id: str) -> ServiceResult:
        """partners.id == profiles.id, então é uma busca direta por id."""
        try:
            response = (
                self.client.table("partners")
                .select(
                    "id, public_slug, campaign_message, telegram_chat_id, "
                    "is_accepting_supporters"
                )
                .eq("id", profile_id)
                .limit(1)
                .execute()
            )
            rows = response.data or []
            return ServiceResult(
                success=True, message="ok", data=rows[0] if rows else None
            )
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível carregar os dados do parceiro.",
            )

    def list_unlinked_partner_profiles(self) -> ServiceResult:
        """Perfis com role=parceiro que ainda não têm registro em partners."""
        try:
            profiles = (
                self.client.table("profiles")
                .select("id, first_name, last_name, email")
                .eq("role", "parceiro")
                .execute()
            ).data or []

            linked = self.client.table("partners").select("id").execute().data or []
            linked_ids = {row["id"] for row in linked}

            unlinked = [p for p in profiles if p["id"] not in linked_ids]
            return ServiceResult(success=True, message="ok", data=unlinked)
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível carregar os perfis disponíveis.",
                data=[],
            )

    def generate_unique_slug(self, seed_text: str) -> str:
        base_slug = slugify(seed_text) or "parceiro"
        candidate = base_slug
        suffix = 1

        while True:
            existing = (
                self.client.table("partners")
                .select("id")
                .eq("public_slug", candidate)
                .limit(1)
                .execute()
            )
            if not existing.data:
                return candidate
            suffix += 1
            candidate = f"{base_slug}-{suffix}"

    def create_partner(
        self,
        profile_id: str,
        created_by: str,
        campaign_message: str = "",
        telegram_chat_id: str = "",
        slug_seed: str = "",
        custom_slug: str | None = None,
    ) -> ServiceResult:
        try:
            final_slug = (
                slugify(custom_slug)
                if custom_slug
                else self.generate_unique_slug(slug_seed)
            )

            response = (
                self.client.table("partners")
                .insert(
                    {
                        "id": profile_id,
                        "public_slug": final_slug,
                        "campaign_message": campaign_message.strip() or None,
                        "telegram_chat_id": telegram_chat_id.strip() or None,
                        "is_accepting_supporters": True,
                        "created_by": created_by,
                    }
                )
                .execute()
            )

            if not response.data:
                return ServiceResult(
                    success=False, message="Não foi possível criar o parceiro."
                )

            log_activity(
                self.client,
                actor_id=created_by,
                entity_type="partner",
                action="created",
                entity_id=profile_id,
                metadata={"public_slug": final_slug},
            )

            return ServiceResult(
                success=True, message="Parceiro criado.", data=response.data[0]
            )
        except Exception as error:
            message = str(error)
            if "public_slug" in message or "duplicate key" in message.lower():
                return ServiceResult(
                    success=False, message="Já existe um parceiro com esse link."
                )
            return ServiceResult(
                success=False, message="Não foi possível criar o parceiro."
            )

    def update_partner(
        self,
        partner_id: str,
        actor_id: str,
        campaign_message: str | None = None,
        telegram_chat_id: str | None = None,
        is_accepting_supporters: bool | None = None,
    ) -> ServiceResult:
        payload: dict[str, Any] = {}
        if campaign_message is not None:
            payload["campaign_message"] = campaign_message.strip() or None
        if telegram_chat_id is not None:
            payload["telegram_chat_id"] = telegram_chat_id.strip() or None
        if is_accepting_supporters is not None:
            payload["is_accepting_supporters"] = is_accepting_supporters

        if not payload:
            return ServiceResult(success=True, message="Nada para atualizar.")

        try:
            response = (
                self.client.table("partners")
                .update(payload)
                .eq("id", partner_id)
                .execute()
            )
            if not response.data:
                return ServiceResult(
                    success=False, message="Não foi possível atualizar o parceiro."
                )

            log_activity(
                self.client,
                actor_id=actor_id,
                entity_type="partner",
                action="updated",
                entity_id=partner_id,
                metadata=payload,
            )

            return ServiceResult(
                success=True, message="Parceiro atualizado.", data=response.data[0]
            )
        except Exception:
            return ServiceResult(
                success=False, message="Não foi possível atualizar o parceiro."
            )
