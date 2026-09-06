import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.config.settings import settings
from src.prompts.assistant import build_public_system_prompt, build_system_prompt


@dataclass
class ServiceResult:
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class AIService:
    """Serviço de Inteligência Artificial com Groq e Supabase.

    Suporta:
    - Modo Público: Visitantes anônimos que consultam projetos e canais oficiais.
    - Modo Autenticado com RLS e Gestão Operacional por Papel:
      1. Parceiro: Acesso aos projetos oficiais + Gestão de suas próprias metas, link e apoiadores cadastrados por ele.
      2. Admin / Super Admin: Acesso aos projetos oficiais + Gestão global de parceiros, metas gerais e volume total de apoiadores.
    """

    def __init__(self, access_token: Optional[str] = None) -> None:
        self.api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        self.model = settings.GROQ_MODEL or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.access_token = access_token

    def _get_authenticated_client(self):
        """Retorna cliente Supabase autenticado respeitando as policies de RLS do usuário."""
        from src.database.supabase_client import get_supabase
        client = get_supabase()
        if self.access_token:
            client.postgrest.auth(self.access_token)
        return client

    def _fetch_business_context_for_role(self, user_id: str, role: str) -> str:
        """Monta o contexto gerencial e em tempo real do banco de dados específico para o papel."""
        client = self._get_authenticated_client()
        blocks = []

        try:
            if role == "parceiro":
                # 1. Dados do Parceiro (Link, mensagem, slug)
                p_res = (
                    client.table("partners")
                    .select("public_slug, campaign_message, is_accepting_supporters")
                    .eq("id", user_id)
                    .limit(1)
                    .execute()
                )
                partner_data = p_res.data[0] if p_res.data else {}
                slug = partner_data.get("public_slug", "")
                base_url = settings.APP_BASE_URL.rstrip("/")
                ref_link = f"{base_url}/?p={slug}" if slug else "Não gerado"

                # 2. Apoiadores cadastrados exclusivamente por este parceiro
                sup_res = (
                    client.table("supporters")
                    .select("first_name, last_name, created_at, whatsapp")
                    .eq("partner_id", user_id)
                    .order("created_at", desc=True)
                    .limit(15)
                    .execute()
                )
                supporters = sup_res.data or []
                total_sup = len(supporters)

                # 3. Metas diárias do parceiro
                from datetime import date
                today_str = date.today().isoformat()
                goal_res = (
                    client.table("daily_goals")
                    .select("target_count, achieved_count, status")
                    .eq("partner_id", user_id)
                    .eq("goal_date", today_str)
                    .limit(1)
                    .execute()
                )
                goal_data = goal_res.data[0] if goal_res.data else None

                blocks.append("### DADOS EXCLUSIVOS DO SEU NEGÓCIO / PARCERIA:")
                blocks.append(f"- Seu Link de Indicação Oficial: {ref_link}")
                blocks.append(f"- Total de Apoiadores Cadastrados por Você: {total_sup}")
                
                if goal_data:
                    blocks.append(
                        f"- Sua Meta de Hoje ({today_str}): Objetivo de {goal_data.get('target_count', 0)} apoiadores | "
                        f"Realizado: {goal_data.get('achieved_count', 0)} | Situação: {goal_data.get('status', 'active')}"
                    )
                else:
                    blocks.append(f"- Sua Meta de Hoje ({today_str}): Nenhuma meta diária registrada para hoje.")

                if supporters:
                    blocks.append("- Últimos apoiadores cadastrados com seu link:")
                    for s in supporters[:6]:
                        blocks.append(f"  • {s.get('first_name', '')} {s.get('last_name', '')} (WhatsApp: {s.get('whatsapp', 'N/D')})")

            elif role in ("admin", "super_admin"):
                # 1. Total Geral de Apoiadores
                sup_cnt = client.table("supporters").select("id", count="exact").execute()
                total_supporters = sup_cnt.count or 0

                # 2. Total e Lista de Parceiros Ativos
                part_res = (
                    client.table("partners")
                    .select("id, public_slug, is_accepting_supporters, profiles!partners_id_fkey(first_name, last_name, email)")
                    .execute()
                )
                partners = part_res.data or []
                total_partners = len(partners)

                blocks.append("### PAINEL GERENCIAL DA CAMPANHA (VISÃO ADMIN):")
                blocks.append(f"- Total Geral de Apoiadores Cadastrados na Campanha: {total_supporters}")
                blocks.append(f"- Total de Parceiros Cadastrados no Sistema: {total_partners}")
                blocks.append("- Lista e desempenho recente dos parceiros:")
                for p in partners[:10]:
                    prof = p.get("profiles") or {}
                    p_name = f"{prof.get('first_name', '')} {prof.get('last_name', '')}".strip() or "Parceiro"
                    p_slug = p.get("public_slug", "")
                    blocks.append(f"  • {p_name} (Slug: {p_slug}) - Aceitando cadastros: {p.get('is_accepting_supporters')}")

        except Exception as exc:
            blocks.append(f"Aviso: Não foi possível carregar os dados gerenciais em tempo real ({exc}).")

        return "\n".join(blocks)

    def _fetch_documents_for_user(self, role: str) -> List[Dict[str, Any]]:
        """Busca documentos da base de conhecimento respeitando o papel do usuário."""
        try:
            client = self._get_authenticated_client()
            res = (
                client.table("knowledge_documents")
                .select("title, content")
                .eq("is_active", True)
                .execute()
            )
            return res.data or []
        except Exception:
            return []

    def _fetch_public_context_documents(self) -> List[Dict[str, Any]]:
        """Busca documentos públicos adicionais no Supabase."""
        try:
            from src.database.supabase_client import get_supabase
            client = get_supabase()
            response = (
                client.table("knowledge_documents")
                .select("title, content")
                .eq("is_active", True)
                .execute()
            )
            return response.data or []
        except Exception:
            return []

    def ask(self, user_id: str, role: str, question: str) -> ServiceResult:
        """
        Modo Autenticado (utilizado em 01__Assistente_IA.py):
        Combina o conhecimento oficial dos projetos do Coronel Henrique com a visão gerencial do papel.
        """
        if not self.api_key:
            return ServiceResult(
                success=False,
                message="Assistente IA não configurado (GROQ_API_KEY ausente no .env).",
            )

        clean_question = question.strip()
        if not clean_question:
            return ServiceResult(success=False, message="Digite uma pergunta.")

        # 1. Documentos teóricos da base de conhecimento
        documents = self._fetch_documents_for_user(role)

        # 2. Injeta os dados operacionais do banco em tempo real de acordo com o papel
        business_context = self._fetch_business_context_for_role(user_id=user_id, role=role)
        if business_context:
            documents.append({"title": f"DADOS DO SEU ACESSO ({role.upper()})", "content": business_context})

        system_prompt = build_system_prompt(documents)

        # 3. Adiciona instrução específica de postura gerencial
        role_instructions = (
            f"\n\nATENÇÃO: O usuário logado possui o papel de {role.upper()}.\n"
            "Ele tem acesso pleno às informações institucionais do Coronel Henrique (22500) "
            "e aos dados operacionais do seu próprio nível de gestão descritos no contexto.\n"
            "Se ele for Parceiro, tire dúvidas sobre os projetos e ajude-o na gestão dos seus apoiadores e metas.\n"
            "Se ele for Admin, tire dúvidas sobre os projetos e auxilie na supervisão geral de parceiros e métricas globais.\n"
            "Nunca misture dados de outros parceiros quando falar com um parceiro individual."
        )
        full_system_prompt = system_prompt + role_instructions

        try:
            from groq import Groq

            groq_client = Groq(api_key=self.api_key)
            completion = groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": full_system_prompt},
                    {"role": "user", "content": clean_question},
                ],
                temperature=0.2,
                max_tokens=800,
            )
            answer = completion.choices[0].message.content or ""

            # Grava no histórico de conversas do usuário se houver tabela ai_conversations
            try:
                client = self._get_authenticated_client()
                client.table("ai_conversations").insert(
                    {
                        "user_id": user_id,
                        "role": role,
                        "question": clean_question,
                        "answer": answer,
                        "sources": [{"title": d.get("title", "")} for d in documents if d.get("title")],
                    }
                ).execute()
            except Exception:
                pass

            return ServiceResult(
                success=True,
                message="ok",
                data={"answer": answer, "sources": documents},
            )

        except Exception as exc:
            return ServiceResult(
                success=False,
                message=f"Não foi possível obter resposta do assistente. Detalhe: {str(exc)}",
            )

    def ask_public(self, question: str) -> ServiceResult:
        """Modo público (visitantes sem login em 11__Fale_com_a_Campanha.py)."""
        if not self.api_key:
            return ServiceResult(
                success=False,
                message="Assistente IA não configurado (GROQ_API_KEY ausente no .env).",
            )

        clean_question = question.strip()
        if not clean_question:
            return ServiceResult(success=False, message="Por favor, digite sua pergunta.")

        documents = self._fetch_public_context_documents()
        system_prompt = build_public_system_prompt(documents)

        try:
            from groq import Groq

            groq_client = Groq(api_key=self.api_key)
            completion = groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": clean_question},
                ],
                temperature=0.2,
                max_tokens=650,
            )
            answer = completion.choices[0].message.content or ""
            return ServiceResult(success=True, message="ok", data={"answer": answer})

        except Exception as exc:
            return ServiceResult(
                success=False,
                message=f"Não foi possível obter resposta do assistente no momento. Detalhe: {str(exc)}",
            )

    def list_own_history(self, user_id: str, limit: int = 10) -> ServiceResult:
        """Recupera histórico pessoal de conversas do usuário logado."""
        try:
            client = self._get_authenticated_client()
            res = (
                client.table("ai_conversations")
                .select("question, answer, sources, created_at")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return ServiceResult(success=True, message="ok", data=res.data or [])
        except Exception:
            return ServiceResult(success=True, message="ok", data=[])
