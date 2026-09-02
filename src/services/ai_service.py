from dataclasses import dataclass
from typing import Any

from src.config.settings import settings
from src.database.supabase_client import get_supabase
from src.prompts.assistant import build_public_system_prompt, build_system_prompt

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


@dataclass
class ServiceResult:
    success: bool
    message: str
    data: Any = None


class AIService:
    """Assistente IA: responde perguntas com base nos knowledge_documents
    visíveis para o papel do usuário e registra cada troca em
    ai_conversations (auditoria).
    """

    def __init__(self, access_token: str | None = None) -> None:
        self.client = get_supabase()
        if access_token:
            self.client.postgrest.auth(access_token)

    def _fetch_context_documents(self, limit: int = 10) -> list[dict[str, Any]]:
        response = (
            self.client.table("knowledge_documents")
            .select("id, title, content")
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def _fetch_public_context_documents(self, limit: int = 10) -> list[dict[str, Any]]:
        """Só documentos marcados is_public — usados pelo Assistente IA sem login."""
        response = (
            self.client.table("knowledge_documents")
            .select("id, title, content")
            .eq("is_public", True)
            .eq("is_active", True)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def _save_conversation(
        self,
        user_id: str,
        role: str,
        question: str,
        answer: str,
        sources: list[dict[str, Any]],
    ) -> None:
        try:
            self.client.table("ai_conversations").insert(
                {
                    "user_id": user_id,
                    "role": role,
                    "question": question,
                    "answer": answer,
                    "sources": sources,
                }
            ).execute()
        except Exception:
            pass

    def ask(self, user_id: str, role: str, question: str) -> ServiceResult:
        if not settings.GROQ_API_KEY:
            return ServiceResult(
                success=False,
                message="Assistente IA não configurado (GROQ_API_KEY ausente no .env).",
            )

        question = question.strip()
        if not question:
            return ServiceResult(success=False, message="Digite uma pergunta.")

        try:
            documents = self._fetch_context_documents()
        except Exception:
            documents = []

        system_prompt = build_system_prompt(documents)
        sources = [{"id": d["id"], "title": d["title"]} for d in documents]

        try:
            from groq import Groq

            groq_client = Groq(api_key=settings.GROQ_API_KEY)
            completion = groq_client.chat.completions.create(
                model=settings.GROQ_MODEL or DEFAULT_GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=0.3,
            )
            answer = completion.choices[0].message.content or ""
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível obter resposta do assistente agora.",
            )

        self._save_conversation(user_id, role, question, answer, sources)

        return ServiceResult(
            success=True,
            message="ok",
            data={"answer": answer, "sources": sources},
        )

    def ask_public(self, question: str) -> ServiceResult:
        """Versão sem login do Assistente IA: só usa documentos is_public e
        não grava histórico (não há user_id — visitante anônimo)."""
        if not settings.GROQ_API_KEY:
            return ServiceResult(
                success=False,
                message="Assistente IA não configurado (GROQ_API_KEY ausente no .env).",
            )

        question = question.strip()
        if not question:
            return ServiceResult(success=False, message="Digite uma pergunta.")

        try:
            documents = self._fetch_public_context_documents()
        except Exception:
            documents = []

        system_prompt = build_public_system_prompt(documents)

        try:
            from groq import Groq

            groq_client = Groq(api_key=settings.GROQ_API_KEY)
            completion = groq_client.chat.completions.create(
                model=settings.GROQ_MODEL or DEFAULT_GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=0.3,
            )
            answer = completion.choices[0].message.content or ""
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível obter resposta do assistente agora.",
            )

        return ServiceResult(success=True, message="ok", data={"answer": answer})

    def list_own_history(self, user_id: str, limit: int = 20) -> ServiceResult:
        try:
            response = (
                self.client.table("ai_conversations")
                .select("id, question, answer, sources, created_at")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return ServiceResult(success=True, message="ok", data=response.data or [])
        except Exception:
            return ServiceResult(
                success=False, message="Não foi possível carregar o histórico."
            )

    def list_all_history(self, limit: int = 100) -> ServiceResult:
        try:
            response = (
                self.client.table("ai_conversations")
                .select(
                    "id, question, answer, role, created_at, "
                    "profiles(first_name, last_name, email)"
                )
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return ServiceResult(success=True, message="ok", data=response.data or [])
        except Exception:
            return ServiceResult(
                success=False, message="Não foi possível carregar o histórico."
            )
