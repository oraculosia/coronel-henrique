-- =============================================================================
-- Promoção controlada do primeiro super_admin
--
-- Pré-requisito: o usuário já existe em auth.users / public.profiles
-- (criado pelo bootstrap Python ou pelo fluxo de cadastro + OTP).
--
-- Substitua o e-mail abaixo ANTES de executar no SQL Editor.
-- Execute uma única vez por ambiente.
-- =============================================================================

do $$
declare
    target_email citext := 'programador.descpro@gmail.com';
    updated_count integer;
begin
    update public.profiles
    set
        first_name = 'William',
        last_name = 'Eustáquio',
        whatsapp = '+5531998417976',
        job_title = 'Desenvolvedor de IA',
        role = 'super_admin',
        verification_status = 'verified',
        is_active = true
    where email = target_email;

    get diagnostics updated_count = row_count;

    if updated_count <> 1 then
        raise exception
            'Nenhum perfil único encontrado para %. Cadastre o usuário antes de promover.',
            target_email;
    end if;
end
$$;
