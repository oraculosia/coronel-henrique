-- =============================================================================
-- Remove o trigger legado que promovia profiles.verification_status para
-- 'verified' automaticamente quando o Supabase Auth confirmava o e-mail
-- (clique no link de confirmação nativo do Supabase). Esse trigger
-- contornava por completo o fluxo de verificação próprio (sql/007) sempre
-- que o "Confirm email" do Supabase estivesse ligado — por isso um usuário
-- conseguia ficar "verified" sem nunca ter usado nosso código por e-mail.
-- =============================================================================

drop trigger if exists on_auth_user_email_confirmed on auth.users;
drop function if exists public.handle_user_email_confirmed();
