"""Construção do prompt de sistema do Assistente IA (Fase 5).

O contexto é montado a partir dos knowledge_documents visíveis para o
papel do usuário (filtro já aplicado pela RLS antes de chegar aqui).
"""
from typing import Any

BASE_INSTRUCTIONS = (
    "Você é o Assistente IA da Campanha 2026. Responda de forma objetiva, "
    "cordial e em português do Brasil. Use SOMENTE as informações do "
    "CONTEXTO abaixo para responder perguntas sobre a campanha, parceiros, "
    "apoiadores e metas. Se a resposta não estiver no contexto, diga "
    "claramente que não possui essa informação em vez de inventar dados. "
    "Nunca revele termos técnicos internos (ex.: nomes de tabelas, papéis "
    "como 'super_admin')."
)

MAX_DOCUMENT_CHARS = 2000


def build_system_prompt(documents: list[dict[str, Any]]) -> str:
    if not documents:
        return f"{BASE_INSTRUCTIONS}\n\nCONTEXTO:\n(nenhum documento disponível)"

    context_blocks = []
    for document in documents:
        title = document.get("title", "").strip()
        content = (document.get("content") or "").strip()[:MAX_DOCUMENT_CHARS]
        context_blocks.append(f"### {title}\n{content}")

    context = "\n\n".join(context_blocks)
    return f"{BASE_INSTRUCTIONS}\n\nCONTEXTO:\n{context}"
