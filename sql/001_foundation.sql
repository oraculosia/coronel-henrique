-- =============================================================================
-- Fase 1 — Fundação
-- Campanha 2026
--
-- Aplicar no SQL Editor do Supabase (role postgres), uma vez por ambiente.
-- O script é idempotente o suficiente para reexecução controlada.
--
-- Regras de segurança:
-- - Papel NÃO vem do metadata do signup (evita escalada de privilégio).
-- - super_admin só nasce pelo script controlado (service_role).
-- - Senhas permanecem no Supabase Auth; nunca nesta schema.
-- =============================================================================

create extension if not exists pgcrypto with schema extensions;
create extension if not exists citext with schema public;

-- -----------------------------------------------------------------------------
-- Enums
-- -----------------------------------------------------------------------------
do $$
begin
    create type public.user_role as enum (
        'super_admin',
        'admin',
        'parceiro',
        'apoiador'
    );
exception
    when duplicate_object then null;
end
$$;

do $$
begin
    create type public.verification_status as enum (
        'pending',
        'verified',
        'blocked',
        'rejected'
    );
exception
    when duplicate_object then null;
end
$$;

-- -----------------------------------------------------------------------------
-- Função de updated_at
-- -----------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

-- -----------------------------------------------------------------------------
-- profiles — 1:1 com auth.users
-- -----------------------------------------------------------------------------
create table if not exists public.profiles (
    id uuid primary key references auth.users (id) on delete cascade,
    first_name text not null default '',
    last_name text not null default '',
    email citext not null,
    whatsapp text,
    job_title text,
    avatar_path text,
    role public.user_role not null default 'parceiro',
    verification_status public.verification_status not null default 'pending',
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint profiles_email_key unique (email)
);

create index if not exists profiles_role_idx
    on public.profiles (role);

create index if not exists profiles_verification_status_idx
    on public.profiles (verification_status);

drop trigger if exists trg_profiles_updated_at on public.profiles;
create trigger trg_profiles_updated_at
    before update on public.profiles
    for each row
    execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- Helpers de autorização (security definer, bypass RLS interno)
-- Nomes confirmados por introspecção direta do banco (pg_proc/pg_policies).
-- -----------------------------------------------------------------------------
create or replace function public.current_user_role()
returns public.user_role
language sql
stable
security definer
set search_path = public
as $$
    select role
    from public.profiles
    where id = auth.uid()
      and is_active = true
$$;

create or replace function public.is_super_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select coalesce(public.current_user_role() = 'super_admin', false)
$$;

create or replace function public.is_admin_or_super_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select coalesce(
        public.current_user_role() in ('super_admin', 'admin'),
        false
    )
$$;

-- -----------------------------------------------------------------------------
-- Trigger: cria profile no signup. Papel fixo = parceiro.
-- NÃO ler raw_user_meta_data.role
-- -----------------------------------------------------------------------------
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    -- Papel é sempre 'parceiro'. Nunca ler role do metadata do cliente.
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
        case
            when new.email_confirmed_at is not null then 'verified'::public.verification_status
            else 'pending'::public.verification_status
        end,
        true
    )
    on conflict (id) do nothing;

    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row
    execute function public.handle_new_user();

create or replace function public.handle_user_email_confirmed()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if new.email_confirmed_at is not null
       and (old.email_confirmed_at is null or old.email_confirmed_at is distinct from new.email_confirmed_at)
    then
        update public.profiles
        set verification_status = 'verified'
        where id = new.id
          and verification_status = 'pending';
    end if;

    return new;
end;
$$;

drop trigger if exists on_auth_user_email_confirmed on auth.users;
create trigger on_auth_user_email_confirmed
    after update of email_confirmed_at on auth.users
    for each row
    execute function public.handle_user_email_confirmed();

-- NOTA DE SEGURANÇA (confirmado por introspecção em 2026-09-01):
-- NÃO existe hoje nenhum trigger que impeça o próprio usuário de alterar
-- `role`/`is_active` via profiles_update_own_limited. Ver seção final deste
-- arquivo. Não implementado ainda — decisão pendente do responsável pelo projeto.

-- -----------------------------------------------------------------------------
-- RLS — profiles
-- Nomes de policy confirmados por introspecção direta (pg_policies).
-- -----------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.profiles force row level security;

drop policy if exists profiles_select_own_or_staff on public.profiles;
create policy profiles_select_own_or_staff
    on public.profiles
    for select
    to authenticated
    using (
        auth.uid() = id
        or public.is_admin_or_super_admin()
    );

drop policy if exists profiles_update_own_limited on public.profiles;
create policy profiles_update_own_limited
    on public.profiles
    for update
    to authenticated
    using (auth.uid() = id)
    with check (auth.uid() = id);

drop policy if exists profiles_staff_manage on public.profiles;
create policy profiles_staff_manage
    on public.profiles
    for all
    to authenticated
    using (public.is_admin_or_super_admin())
    with check (public.is_admin_or_super_admin());

-- -----------------------------------------------------------------------------
-- Grants
-- -----------------------------------------------------------------------------
grant usage on schema public to anon, authenticated;

grant execute on function public.current_user_role() to authenticated;
grant execute on function public.is_super_admin() to authenticated;
grant execute on function public.is_admin_or_super_admin() to authenticated;

revoke all on table public.profiles from anon, public;
grant select, update on table public.profiles to authenticated;

-- As tabelas de Fase 3 (partners, supporters, daily_goals, activity_logs,
-- ai_conversations, knowledge_documents) e suas funções/policies reais
-- estão documentadas em sql/004_partners_supporters_goals.sql — foram
-- criadas separadamente e confirmadas via introspecção, não por este arquivo.

