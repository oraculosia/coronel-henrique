"""Testes estruturais da Fase 5 (Assistente IA): valida que o schema de
ai_conversations e knowledge_documents documentado em
sql/004_partners_supporters_goals.sql cobre RLS por papel e auditoria."""
from __future__ import annotations

from src.config.settings import ROOT_DIR

SCHEMA_SQL_PATH = ROOT_DIR / "sql" / "004_partners_supporters_goals.sql"


def _schema_sql() -> str:
    return SCHEMA_SQL_PATH.read_text(encoding="utf-8")


def test_ai_conversations_table_has_audit_columns() -> None:
    sql = _schema_sql().lower()
    block = sql.split("create table if not exists public.ai_conversations")[1]
    block = block.split(";")[0]
    assert "user_id uuid references public.profiles (id)" in block
    assert "question text not null" in block
    assert "answer text not null" in block
    assert "sources jsonb not null default '[]'::jsonb" in block


def test_knowledge_documents_table_has_audience_roles_and_active_flag() -> None:
    sql = _schema_sql().lower()
    block = sql.split("create table if not exists public.knowledge_documents")[1]
    block = block.split(";")[0]
    assert "audience_roles public.user_role[] not null" in block
    assert "is_active boolean not null default true" in block


def test_ai_conversations_policies_restrict_to_own_or_staff() -> None:
    sql = _schema_sql().lower()
    block = sql.split("create policy ai_conversations_select_own_or_staff")[1]
    block = block.split("drop policy if exists ai_conversations_staff_manage")[0]
    assert "user_id = auth.uid()" in block
    assert "is_admin_or_super_admin()" in block


def test_knowledge_documents_select_policy_filters_by_role_and_active() -> None:
    sql = _schema_sql().lower()
    block = sql.split("create policy knowledge_documents_select_by_role")[1]
    block = block.split("drop policy if exists knowledge_documents_staff_manage")[0]
    assert "is_active = true" in block
    assert "current_user_role() = any (audience_roles)" in block
