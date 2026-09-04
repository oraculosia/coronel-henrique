from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.database.supabase_client import get_supabase


@dataclass
class ServiceResult:
    success: bool
    message: str
    data: Any = None


class SupporterService:
    """Cadastro público de apoiadores (INSERT direto, sem RPC) e consulta
    autenticada por parceiro.

    supporters não tem coluna de e-mail; whatsapp é obrigatório.
    A policy supporters_public_insert exige consent_lgpd=true, consent_at
    preenchido e is_public_partner_signup_valid(partner_id, source_slug).
    """

    def __init__(self, access_token: str | None = None) -> None:
        self.client = get_supabase()
        if access_token:
            self.client.postgrest.auth(access_token)

    def resolve_partner_by_slug(self, slug: str) -> ServiceResult:
        try:
            response = (
                self.client.table("partners")
                .select("id, public_slug, campaign_message, is_accepting_supporters")
                .eq("public_slug", slug)
                .eq("is_accepting_supporters", True)
                .limit(1)
                .execute()
            )
            rows = response.data or []
            if not rows:
                return ServiceResult(
                    success=False,
                    message="Link de parceiro não encontrado ou inativo.",
                )
            return ServiceResult(success=True, message="ok", data=rows[0])
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível localizar este link agora.",
            )

    def register_public(
        self,
        partner_id: str,
        slug: str,
        first_name: str,
        last_name: str,
        whatsapp: str,
        consent_lgpd: bool,
        source_utm: dict[str, Any] | None = None,
        avatar_path: str = "",
    ) -> ServiceResult:
        if not consent_lgpd:
            return ServiceResult(
                success=False,
                message="É necessário aceitar o uso dos dados (LGPD) para continuar.",
            )

        try:
            payload = {
                "partner_id": partner_id,
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "whatsapp": whatsapp,
                "avatar_path": avatar_path or None,
                "source_slug": slug,
                "source_utm": source_utm or {},
                "consent_lgpd": True,
                "consent_at": datetime.now(timezone.utc).isoformat(),
                "is_valid": True,
            }

            response = self.client.table("supporters").insert(payload).execute()

            rows = response.data or []
            if not rows:
                return ServiceResult(
                    success=False, message="Não foi possível concluir o cadastro."
                )

            return ServiceResult(
                success=True,
                message="Cadastro realizado com sucesso!",
                data=rows[0],
            )

        except Exception:
            return ServiceResult(
                success=False,
                message=(
                    "Não foi possível concluir o cadastro. Verifique o link "
                    "e tente novamente."
                ),
            )

    def list_for_partner(self, partner_id: str) -> ServiceResult:
        try:
            response = (
                self.client.table("supporters")
                .select(
                    "id, first_name, last_name, whatsapp, is_valid, created_at"
                )
                .eq("partner_id", partner_id)
                .order("created_at", desc=True)
                .execute()
            )
            return ServiceResult(success=True, message="ok", data=response.data or [])
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível carregar os apoiadores.",
                data=[],
            )

    def count_for_partner(self, partner_id: str) -> ServiceResult:
        try:
            response = (
                self.client.table("supporters")
                .select("id", count="exact")
                .eq("partner_id", partner_id)
                .limit(1)
                .execute()
            )
            return ServiceResult(success=True, message="ok", data=response.count or 0)
        except Exception:
            return ServiceResult(
                success=False, message="Não foi possível contar os apoiadores.", data=0
            )

    def list_all_for_staff(self) -> ServiceResult:
        """Todos os apoiadores, com o parceiro de origem. Só admin/super_admin
        (policy supporters_staff_manage)."""
        try:
            response = (
                self.client.table("supporters")
                .select(
                    "id, first_name, last_name, whatsapp, is_valid, created_at, "
                    "partner_id, partners(public_slug, profiles!partners_id_fkey(first_name, last_name))"
                )
                .order("created_at", desc=True)
                .execute()
            )
            return ServiceResult(success=True, message="ok", data=response.data or [])
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível carregar os apoiadores.",
                data=[],
            )


def find_duplicate_whatsapp(supporters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa apoiadores pelo mesmo whatsapp. Retorna só os grupos com 2+
    registros — candidatos a cadastro duplicado."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for supporter in supporters:
        whatsapp = supporter.get("whatsapp")
        if not whatsapp:
            continue
        groups.setdefault(whatsapp, []).append(supporter)

    return [
        {"whatsapp": whatsapp, "count": len(rows), "supporters": rows}
        for whatsapp, rows in groups.items()
        if len(rows) > 1
    ]
