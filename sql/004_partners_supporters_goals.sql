-- =============================================================================
-- Fase 3 — Operação da campanha
-- Campanha 2026
--
-- Este arquivo DOCUMENTA o schema real, já instalado no projeto Supabase,
-- confirmado em 2026-09-01 por introspecção direta (pg_proc, pg_policies,
-- information_schema.triggers/routines, pg_indexes). Foi criado
-- originalmente por um script fora deste repositório; este arquivo existe
-- para que um ambiente novo possa ser reproduzido de forma idêntica.
--
-- Todo o conteúdo é idempotente (create table if not exists, create or
-- replace function, drop policy/trigger if exists + create) — seguro
-- reexecutar mesmo já estando tudo instalado.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Enum de status da meta diária
-- -----------------------------------------------------------------------------
do $$
begin
    create type public.goal_status as enum (
        'active',
        'achieved',
        'expired',
        'cancelled'
    );
exception
    when duplicate_object then null;
end
$$;

-- -----------------------------------------------------------------------------
-- partners
-- partners.id é o MESMO id do profile do parceiro (não existe profile_id).
-- -----------------------------------------------------------------------------
create table if not exists public.partners (
    id uuid primary key references public.profiles (id) on delete cascade,
    public_slug text not null,
    campaign_message text,
    telegram_chat_id text,
    is_accepting_supporters boolean not null default true,
    created_by uuid references public.profiles (id) on delete set null,
    created_at timestamptz not null default timezone('utc'::text, now()),
    updated_at timestamptz not null default timezone('utc'::text, now()),
    constraint partners_public_slug_key unique (public_slug)
);

create index if not exists idx_partners_slug on public.partners (public_slug);

drop trigger if exists trg_partners_updated_at on public.partners;
create trigger trg_partners_updated_at
    before update on public.partners
    for each row
    execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- supporters
-- Não existe coluna de e-mail. whatsapp é obrigatório. Sem dedupe por DB.
-- -----------------------------------------------------------------------------
create table if not exists public.supporters (
    id uuid primary key default gen_random_uuid(),
    partner_id uuid references public.partners (id) on delete cascade,
    first_name text not null,
    last_name text not null,
    whatsapp text not null,
    avatar_path text,
    source_slug text,
    source_utm jsonb not null default '{}'::jsonb,
    consent_lgpd boolean not null default false,
    consent_at timestamptz,
    is_valid boolean not null default true,
    reviewed_by uuid references public.profiles (id) on delete set null,
    reviewed_at timestamptz,
    created_at timestamptz not null default timezone('utc'::text, now()),
    updated_at timestamptz not null default timezone('utc'::text, now())
);

create index if not exists idx_supporters_partner_created_at
    on public.supporters (partner_id, created_at desc);
create index if not exists idx_supporters_created_at
    on public.supporters (created_at desc);
create index if not exists idx_supporters_whatsapp
    on public.supporters (whatsapp);

drop trigger if exists trg_supporters_updated_at on public.supporters;
create trigger trg_supporters_updated_at
    before update on public.supporters
    for each row
    execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- daily_goals
-- -----------------------------------------------------------------------------
create table if not exists public.daily_goals (
    id uuid primary key default gen_random_uuid(),
    partner_id uuid not null references public.partners (id) on delete cascade,
    goal_date date not null default current_date,
    target_count integer not null,
    achieved_count integer not null default 0,
    status public.goal_status not null default 'active',
    notified_at timestamptz,
    created_by uuid references public.profiles (id) on delete set null,
    created_at timestamptz not null default timezone('utc'::text, now()),
    updated_at timestamptz not null default timezone('utc'::text, now()),
    constraint daily_goals_unique_partner_date unique (partner_id, goal_date)
);

create index if not exists idx_daily_goals_partner_date
    on public.daily_goals (partner_id, goal_date desc);
create index if not exists idx_daily_goals_status
    on public.daily_goals (status);

drop trigger if exists trg_daily_goals_updated_at on public.daily_goals;
create trigger trg_daily_goals_updated_at
    before update on public.daily_goals
    for each row
    execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- activity_logs
-- -----------------------------------------------------------------------------
create table if not exists public.activity_logs (
    id uuid primary key default gen_random_uuid(),
    actor_id uuid references public.profiles (id) on delete set null,
    entity_type text not null,
    entity_id uuid,
    action text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default timezone('utc'::text, now())
);

create index if not exists idx_activity_logs_actor_created_at
    on public.activity_logs (actor_id, created_at desc);
create index if not exists idx_activity_logs_entity
    on public.activity_logs (entity_type, entity_id);

-- -----------------------------------------------------------------------------
-- ai_conversations — Fase 5 (Assistente IA), documentado aqui por completude
-- -----------------------------------------------------------------------------
create table if not exists public.ai_conversations (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references public.profiles (id) on delete cascade,
    role public.user_role not null,
    question text not null,
    answer text not null,
    sources jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default timezone('utc'::text, now())
);

-- -----------------------------------------------------------------------------
-- knowledge_documents — Fase 5, documentado aqui por completude
-- -----------------------------------------------------------------------------
create table if not exists public.knowledge_documents (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    content text not null,
    audience_roles public.user_role[] not null default array['super_admin']::public.user_role[],
    is_active boolean not null default true,
    created_by uuid references public.profiles (id) on delete set null,
    updated_by uuid references public.profiles (id) on delete set null,
    created_at timestamptz not null default timezone('utc'::text, now()),
    updated_at timestamptz not null default timezone('utc'::text, now())
);

-- -----------------------------------------------------------------------------
-- Funções de autorização/validação específicas da Fase 3
-- -----------------------------------------------------------------------------
create or replace function public.is_partner_of(target_partner_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $function$
    select target_partner_id = auth.uid()
$function$;

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
          and profile.role = 'parceiro'::public.user_role
    );
$function$;

-- -----------------------------------------------------------------------------
-- Trigger: incrementa a meta do dia a cada novo apoiador válido.
-- Só atualiza se já existir uma linha de daily_goals para o dia (não cria).
-- -----------------------------------------------------------------------------
create or replace function public.increment_partner_daily_goal()
returns trigger
language plpgsql
security definer
set search_path = ''
as $function$
declare
    goal_record public.daily_goals;
begin
    if new.partner_id is null or new.is_valid = false then
        return new;
    end if;

    update public.daily_goals
    set
        achieved_count = achieved_count + 1,
        status = case
            when achieved_count + 1 >= target_count
                then 'achieved'::public.goal_status
            else status
        end,
        updated_at = timezone('utc'::text, now())
    where partner_id = new.partner_id
      and goal_date = current_date
      and status in (
          'active'::public.goal_status,
          'achieved'::public.goal_status
      )
    returning * into goal_record;

    return new;
end;
$function$;

drop trigger if exists trg_increment_partner_daily_goal on public.supporters;
create trigger trg_increment_partner_daily_goal
    after insert on public.supporters
    for each row
    execute procedure public.increment_partner_daily_goal();

-- -----------------------------------------------------------------------------
-- RLS
-- -----------------------------------------------------------------------------
alter table public.partners enable row level security;
alter table public.supporters enable row level security;
alter table public.daily_goals enable row level security;
alter table public.activity_logs enable row level security;
alter table public.ai_conversations enable row level security;
alter table public.knowledge_documents enable row level security;

-- partners
drop policy if exists partners_owner_update on public.partners;
create policy partners_owner_update
    on public.partners
    for update
    to authenticated
    using (public.is_partner_of(partners.id))
    with check (public.is_partner_of(partners.id));

drop policy if exists partners_staff_manage on public.partners;
create policy partners_staff_manage
    on public.partners
    for all
    to authenticated
    using (public.is_admin_or_super_admin())
    with check (public.is_admin_or_super_admin());

drop policy if exists partners_staff_select_all on public.partners;
create policy partners_staff_select_all
    on public.partners
    for select
    to authenticated
    using (
        public.is_admin_or_super_admin()
        or public.is_partner_of(partners.id)
    );

-- supporters
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
        and (
            select public.is_public_partner_signup_valid(
                supporters.partner_id,
                supporters.source_slug
            )
        )
    );

drop policy if exists supporters_partner_update_own on public.supporters;
create policy supporters_partner_update_own
    on public.supporters
    for update
    to authenticated
    using (
        partner_id = auth.uid()
        and public.current_user_role() = 'parceiro'::public.user_role
    )
    with check (
        partner_id = auth.uid()
        and public.current_user_role() = 'parceiro'::public.user_role
    );

drop policy if exists supporters_select_by_access on public.supporters;
create policy supporters_select_by_access
    on public.supporters
    for select
    to authenticated
    using (
        public.is_admin_or_super_admin()
        or (
            partner_id = auth.uid()
            and public.current_user_role() = 'parceiro'::public.user_role
        )
    );

drop policy if exists supporters_staff_manage on public.supporters;
create policy supporters_staff_manage
    on public.supporters
    for all
    to authenticated
    using (public.is_admin_or_super_admin())
    with check (public.is_admin_or_super_admin());

-- daily_goals
drop policy if exists daily_goals_partner_create_own on public.daily_goals;
create policy daily_goals_partner_create_own
    on public.daily_goals
    for insert
    to authenticated
    with check (
        public.is_partner_of(daily_goals.partner_id)
        and created_by = auth.uid()
    );

drop policy if exists daily_goals_partner_update_own on public.daily_goals;
create policy daily_goals_partner_update_own
    on public.daily_goals
    for update
    to authenticated
    using (public.is_partner_of(daily_goals.partner_id))
    with check (public.is_partner_of(daily_goals.partner_id));

drop policy if exists daily_goals_select_by_access on public.daily_goals;
create policy daily_goals_select_by_access
    on public.daily_goals
    for select
    to authenticated
    using (
        public.is_admin_or_super_admin()
        or public.is_partner_of(daily_goals.partner_id)
    );

drop policy if exists daily_goals_staff_manage on public.daily_goals;
create policy daily_goals_staff_manage
    on public.daily_goals
    for all
    to authenticated
    using (public.is_admin_or_super_admin())
    with check (public.is_admin_or_super_admin());

-- activity_logs
drop policy if exists activity_logs_authenticated_insert_own on public.activity_logs;
create policy activity_logs_authenticated_insert_own
    on public.activity_logs
    for insert
    to authenticated
    with check (actor_id = auth.uid());

drop policy if exists activity_logs_staff_select on public.activity_logs;
create policy activity_logs_staff_select
    on public.activity_logs
    for select
    to authenticated
    using (public.is_admin_or_super_admin());

-- ai_conversations
drop policy if exists ai_conversations_insert_own on public.ai_conversations;
create policy ai_conversations_insert_own
    on public.ai_conversations
    for insert
    to authenticated
    with check (
        user_id = auth.uid()
        and role = public.current_user_role()
    );

drop policy if exists ai_conversations_select_own_or_staff on public.ai_conversations;
create policy ai_conversations_select_own_or_staff
    on public.ai_conversations
    for select
    to authenticated
    using (
        user_id = auth.uid()
        or public.is_admin_or_super_admin()
    );

drop policy if exists ai_conversations_staff_manage on public.ai_conversations;
create policy ai_conversations_staff_manage
    on public.ai_conversations
    for all
    to authenticated
    using (public.is_admin_or_super_admin())
    with check (public.is_admin_or_super_admin());

-- knowledge_documents
drop policy if exists knowledge_documents_select_by_role on public.knowledge_documents;
create policy knowledge_documents_select_by_role
    on public.knowledge_documents
    for select
    to authenticated
    using (
        is_active = true
        and public.current_user_role() = any (audience_roles)
    );

drop policy if exists knowledge_documents_staff_manage on public.knowledge_documents;
create policy knowledge_documents_staff_manage
    on public.knowledge_documents
    for all
    to authenticated
    using (public.is_admin_or_super_admin())
    with check (public.is_admin_or_super_admin());

