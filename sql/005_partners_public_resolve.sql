-- =============================================================================
-- Fase 3 — Link público: resolver slug -> partner_id sem login
--
-- Contexto: supporters_public_insert exige que o cliente já envie o
-- partner_id (uuid) junto com o source_slug — não existe policy de SELECT
-- para anon em partners, então a página pública não tinha como descobrir
-- o partner_id a partir do slug do link.
--
-- IMPORTANTE: neste projeto, TODAS as tabelas têm grant amplo padrão do
-- Supabase para anon/authenticated (ALTER DEFAULT PRIVILEGES = arwdDxtm),
-- ou seja, GRANT SELECT (colunas) sozinho NÃO restringe nada — o grant
-- de tabela inteira já preexistente prevalece. Por isso o REVOKE abaixo
-- é obrigatório antes do GRANT column-level; sem ele, telegram_chat_id
-- e created_by ficariam expostos ao anon assim que a policy de SELECT
-- libera a linha.
-- =============================================================================

drop policy if exists partners_public_resolve_by_slug on public.partners;
create policy partners_public_resolve_by_slug
    on public.partners
    for select
    to anon
    using (is_accepting_supporters = true);

revoke all on table public.partners from anon;

grant select (id, public_slug, campaign_message, is_accepting_supporters)
    on table public.partners
    to anon;
