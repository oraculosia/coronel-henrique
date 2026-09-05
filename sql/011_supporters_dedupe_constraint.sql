-- =============================================================================
-- Fase 3+ — Bloqueio de cadastro duplicado de apoiador (mesmo parceiro)
--
-- Contexto: o cadastro público de apoiadores é um INSERT direto (anon), sem
-- RPC e sem policy de SELECT para anon em supporters — por isso a checagem
-- de duplicidade não pode ser feita no cliente antes do INSERT (a policy
-- supporters_select_by_access só libera para authenticated dono/staff).
-- A solução é um índice único no banco: mesmo nome+sobrenome (case-insensitive)
-- + whatsapp para o mesmo parceiro faz o INSERT falhar com unique_violation,
-- que o SupporterService.register_public já traduz numa mensagem amigável.
-- =============================================================================

create unique index if not exists supporters_unique_name_whatsapp_per_partner
    on public.supporters (partner_id, lower(first_name), lower(last_name), whatsapp);
