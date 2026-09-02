-- =============================================================================
-- Correção: cargo profissional (job_title)
--
-- Causa do erro "Database error creating new user":
-- 001_foundation.sql foi aplicado ANTES de job_title existir.
-- CREATE TABLE IF NOT EXISTS não adiciona colunas depois.
-- O trigger handle_new_user passou a inserir job_title e o Auth desfaz o usuário.
--
-- Execute este arquivo no SQL Editor do Supabase e rode de novo:
--   python scripts/bootstrap_super_admin.py
-- =============================================================================

alter table public.profiles
    add column if not exists job_title text;

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
