-- =============================================================================
-- Fase 3+ — E-mail do apoiador (envio do template de boas-vindas)
--
-- Contexto: supporters não tinha coluna de e-mail (só whatsapp). Para o
-- template de boas-vindas chegar a todos os novos apoiadores, o cadastro
-- público passou a exigir e-mail. Coluna fica nullable (linhas antigas não
-- têm e-mail), mas a policy de INSERT público exige preenchido daqui pra
-- frente.
-- =============================================================================

alter table public.supporters
    add column if not exists email citext;

drop policy if exists supporters_public_insert on public.supporters;
create policy supporters_public_insert
    on public.supporters
    for insert
    to anon, authenticated
    with check (
        consent_lgpd = true
        and consent_at is not null
        and is_valid = true
        and partner_id is not null
        and source_slug is not null
        and email is not null
        and (
            select public.is_public_partner_signup_valid(
                supporters.partner_id,
                supporters.source_slug
            )
        )
    );
