from typing import Any


def log_activity(
    client: Any,
    actor_id: str,
    entity_type: str,
    action: str,
    entity_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Grava um evento em activity_logs usando um client já autenticado.

    Best-effort: nunca lança exceção, para não quebrar a operação
    principal que está sendo registrada (ex.: criar parceiro/meta).
    """
    try:
        client.table("activity_logs").insert(
            {
                "actor_id": actor_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "metadata": metadata or {},
            }
        ).execute()
    except Exception:
        pass
