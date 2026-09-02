-- =============================================================================
-- Inclui avatar_path (foto de perfil) na criação automática de profile.
-- A foto é enviada no cadastro (Criar Conta) já como caminho salvo local,
-- e o trigger só grava o texto do caminho vindo do metadata do Auth.
-- =============================================================================

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
