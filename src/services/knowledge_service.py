from dataclasses import dataclass
from typing import Any

from src.database.supabase_client import get_supabase
from src.services.activity_log_service import log_activity


@dataclass
class ServiceResult:
    success: bool
    message: str
    data: Any = None


class KnowledgeService:
    """Base de conhecimento usada pelo Assistente IA (knowledge_documents).

    Leitura por papel é resolvida pela própria RLS
    (knowledge_documents_select_by_role: is_active + papel em audience_roles).
    Staff (admin/super_admin) enxerga e gerencia tudo via
    knowledge_documents_staff_manage.
    """

    def __init__(self, access_token: str) -> None:
        self.client = get_supabase()
        self.client.postgrest.auth(access_token)

    def list_for_role(self, limit: int = 20) -> ServiceResult:
        try:
            response = (
                self.client.table("knowledge_documents")
                .select("id, title, content, audience_roles, updated_at")
                .order("updated_at", desc=True)
                .limit(limit)
                .execute()
            )
            return ServiceResult(success=True, message="ok", data=response.data or [])
        except Exception:
            return ServiceResult(
                success=False, message="Não foi possível carregar a base de conhecimento."
            )

    def list_all_for_staff(self) -> ServiceResult:
        try:
            response = (
                self.client.table("knowledge_documents")
                .select(
                    "id, title, content, audience_roles, is_active, is_public, "
                    "created_at, updated_at"
                )
                .order("updated_at", desc=True)
                .execute()
            )
            return ServiceResult(success=True, message="ok", data=response.data or [])
        except Exception:
            return ServiceResult(
                success=False, message="Não foi possível carregar os documentos."
            )

    def create_document(
        self,
        title: str,
        content: str,
        audience_roles: list[str],
        created_by: str,
        is_public: bool = False,
    ) -> ServiceResult:
        try:
            response = (
                self.client.table("knowledge_documents")
                .insert(
                    {
                        "title": title.strip(),
                        "content": content.strip(),
                        "audience_roles": audience_roles,
                        "is_public": is_public,
                        "created_by": created_by,
                        "updated_by": created_by,
                    }
                )
                .execute()
            )
            rows = response.data or []
            document = rows[0] if rows else None
            log_activity(
                self.client,
                actor_id=created_by,
                entity_type="knowledge_document",
                action="created",
                entity_id=document.get("id") if document else None,
                metadata={"title": title.strip()},
            )
            return ServiceResult(
                success=True, message="Documento criado.", data=document
            )
        except Exception:
            return ServiceResult(
                success=False, message="Não foi possível criar o documento."
            )

    def update_document(
        self,
        document_id: str,
        actor_id: str,
        title: str | None = None,
        content: str | None = None,
        audience_roles: list[str] | None = None,
        is_active: bool | None = None,
        is_public: bool | None = None,
    ) -> ServiceResult:
        payload: dict[str, Any] = {"updated_by": actor_id}
        if title is not None:
            payload["title"] = title.strip()
        if content is not None:
            payload["content"] = content.strip()
        if audience_roles is not None:
            payload["audience_roles"] = audience_roles
        if is_active is not None:
            payload["is_active"] = is_active
        if is_public is not None:
            payload["is_public"] = is_public

        try:
            self.client.table("knowledge_documents").update(payload).eq(
                "id", document_id
            ).execute()
            log_activity(
                self.client,
                actor_id=actor_id,
                entity_type="knowledge_document",
                action="updated",
                entity_id=document_id,
                metadata={"fields": list(payload.keys())},
            )
            return ServiceResult(success=True, message="Documento atualizado.")
        except Exception:
            return ServiceResult(
                success=False, message="Não foi possível atualizar o documento."
            )
