-- =============================================================================
-- Base de conhecimento pública — usada pelo Assistente IA institucional
-- (pages/11, sem login), separada do conteúdo interno por papel.
-- =============================================================================

alter table public.knowledge_documents
    add column if not exists is_public boolean not null default false;

drop policy if exists knowledge_documents_public_select on public.knowledge_documents;
create policy knowledge_documents_public_select
    on public.knowledge_documents
    for select
    to anon
    using (is_active and is_public);
