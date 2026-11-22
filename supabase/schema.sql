-- Engineering Degree OS - Cloud Feedback table.
-- Run once in the SQL Editor of a NEW Supabase project (already applied to project lsyjwixpiqtwczzzcjub
-- as migration "create_app_feedback"). Do not re-run over an existing table.
begin;

create table public.app_feedback (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid()
        references auth.users(id) on delete cascade,
    name text not null
        check (char_length(btrim(name)) between 1 and 100),
    message text not null
        check (char_length(btrim(message)) between 1 and 2000),
    created_at timestamptz not null default now()
);

alter table public.app_feedback enable row level security;

revoke all on table public.app_feedback from anon, authenticated;
grant usage on schema public to authenticated;
grant select, insert on table public.app_feedback to authenticated;

create policy "Read own feedback"
on public.app_feedback for select
to authenticated
using ((select auth.uid()) = user_id);

create policy "Insert own feedback"
on public.app_feedback for insert
to authenticated
with check ((select auth.uid()) = user_id);

create index app_feedback_user_created_idx
on public.app_feedback (user_id, created_at desc);

commit;
