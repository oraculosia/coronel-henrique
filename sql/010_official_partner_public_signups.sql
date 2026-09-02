-- =============================================================================
-- Conta institucional "Campanha Oficial" para atribuir apoiadores cadastrados
-- pelo Assistente IA público (pages/11), que não vem de um link de parceiro
-- específico. Atribuído ao super_admin (William Eustáquio), a pedido do
-- responsável pelo projeto.
--
-- is_public_partner_signup_valid exigia role='parceiro' — abaixo passa a
-- aceitar também 'super_admin', só pra esse caso institucional.
-- =============================================================================

create or replace function public.is_public_partner_signup_valid(
    target_partner_id uuid,
    submitted_slug text
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $function$
    select exists (
        select 1
        from public.partners partner
        join public.profiles profile on profile.id = partner.id
        where partner.id = target_partner_id
          and partner.public_slug = submitted_slug
          and partner.is_accepting_supporters = true
          and profile.is_active = true
          and profile.verification_status = 'verified'::public.verification_status
          and profile.role in (
              'parceiro'::public.user_role,
              'super_admin'::public.user_role
          )
    );
$function$;

insert into public.partners (id, public_slug, campaign_message, is_accepting_supporters, created_by)
select
    id,
    'campanha-oficial',
    'Cadastro pelo Assistente IA público da Campanha 2026',
    true,
    id
from public.profiles
where email = 'programador.descpro@gmail.com'
on conflict (id) do update
    set is_accepting_supporters = true;
