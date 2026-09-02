-- =============================================================================
-- Verificação de e-mail própria (não usa mais o e-mail de confirmação do
-- Supabase Auth). Requer o toggle "Confirm email" desligado em
-- Authentication > Providers > Email no painel do Supabase — com o toggle
-- ligado, o Supabase marca email_confirmed_at na hora e o gate abaixo perde
-- o efeito.
-- =============================================================================

create table if not exists public.email_verification_codes (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    code_hash text not null,
    expires_at timestamptz not null,
    consumed_at timestamptz,
    created_at timestamptz not null default now()
);

create index if not exists email_verification_codes_user_id_idx
    on public.email_verification_codes (user_id);

alter table public.email_verification_codes enable row level security;
-- Sem policies para anon/authenticated: só o service_role (que ignora RLS)
-- grava e lê essa tabela — toda a validação do código passa pelo backend.

-- Com o e-mail de confirmação do Supabase desativado, email_confirmed_at é
-- preenchido automaticamente no cadastro. O perfil deve nascer sempre
-- "pending"; só o fluxo próprio (email_verification_codes) promove a
-- 'verified'.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.profiles (
        id,
        first_name,
        last_name,
        email,
        whatsapp,
        job_title,
        avatar_path,
        role,
        verification_status,
        is_active
    )
    values (
        new.id,
        coalesce(new.raw_user_meta_data ->> 'first_name', ''),
        coalesce(new.raw_user_meta_data ->> 'last_name', ''),
        coalesce(new.email, ''),
        nullif(new.raw_user_meta_data ->> 'whatsapp', ''),
        nullif(new.raw_user_meta_data ->> 'job_title', ''),
        nullif(new.raw_user_meta_data ->> 'avatar_path', ''),
        'parceiro',
        'pending'::public.verification_status,
        true
    )
    on conflict (id) do nothing;

    return new;
end;
$$;
