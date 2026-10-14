-- NeuralHUD / Media Automation State Engine schema.
--
-- Every status change goes through transition_job(), whether it comes from a
-- webhook, a worker, or the MCP server. That one function is what keeps state
-- changes atomic and the state machine honest.
--
-- Safe to re-run: objects are created only if missing.

create extension if not exists pgcrypto;

do $$ begin
  create type job_status as enum (
    'queued',          -- script accepted, nothing spent yet
    'tts_pending',     -- ElevenLabs synthesis requested  (SPENDS CREDITS)
    'tts_done',        -- audio asset registered
    'render_pending',  -- Remotion render requested       (SPENDS CREDITS)
    'rendered',        -- MP4 asset registered
    'delivered',       -- handed to review dashboard (terminal)
    'failed',          -- stopped; failed_stage records where
    'cancelled'        -- terminal
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type asset_kind as enum ('audio', 'remotion_project', 'video');
exception when duplicate_object then null; end $$;

do $$ begin
  create type gen_provider as enum ('elevenlabs', 'remotion');
exception when duplicate_object then null; end $$;

do $$ begin
  create type gen_status as enum ('started', 'succeeded', 'failed');
exception when duplicate_object then null; end $$;

create table if not exists jobs (
  id                uuid primary key default gen_random_uuid(),
  idempotency_key   text not null unique,
  title             text not null,
  script_text       text not null,
  script_hash       text not null,  -- set by jobs_set_script_hash trigger
  status            job_status not null default 'queued',
  failed_stage      job_status,
  last_error        text,
  attempt           integer not null default 0,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  status_changed_at timestamptz not null default now()
);
-- convert_to() isn't immutable, so a generated column can't use it; a trigger can.
create or replace function jobs_set_script_hash() returns trigger
language plpgsql as $$
begin
  new.script_hash := encode(sha256(convert_to(new.script_text, 'UTF8')), 'hex');
  return new;
end $$;

drop trigger if exists jobs_script_hash on jobs;
create trigger jobs_script_hash before insert or update of script_text on jobs
  for each row execute function jobs_set_script_hash();

create index if not exists jobs_status_idx on jobs (status, status_changed_at);
create index if not exists jobs_script_hash_idx on jobs (script_hash);

create table if not exists job_events (
  id          bigserial primary key,
  job_id      uuid not null references jobs (id) on delete cascade,
  from_status job_status,
  to_status   job_status not null,
  actor       text not null,
  reason      text,
  created_at  timestamptz not null default now()
);
create index if not exists job_events_job_idx on job_events (job_id, created_at);
create index if not exists job_events_to_idx on job_events (to_status, created_at);

create table if not exists assets (
  id         uuid primary key default gen_random_uuid(),
  job_id     uuid not null references jobs (id) on delete cascade,
  kind       asset_kind not null,
  url        text not null,
  metadata   jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (job_id, kind, url)
);

-- One row per paid provider call. Workers MUST write a row before calling
-- ElevenLabs/Remotion and mark it succeeded/failed afterwards. For ElevenLabs,
-- request_hash MUST equal jobs.script_hash so regeneration can be detected.
create table if not exists generation_calls (
  id              uuid primary key default gen_random_uuid(),
  job_id          uuid not null references jobs (id) on delete cascade,
  provider        gen_provider not null,
  request_hash    text not null,
  idempotency_key text not null unique,
  status          gen_status not null default 'started',
  cost_units      numeric not null default 0,
  created_at      timestamptz not null default now(),
  completed_at    timestamptz
);
create index if not exists generation_calls_job_idx on generation_calls (job_id, provider, request_hash);
create index if not exists generation_calls_created_idx on generation_calls (created_at);

-- Write-side idempotency for MCP tools: a replayed key returns the stored result.
create table if not exists mcp_requests (
  idempotency_key text primary key,
  tool            text not null,
  request_hash    text not null,
  response        jsonb,
  actor           text not null,
  created_at      timestamptz not null default now()
);

create table if not exists allowed_transitions (
  from_status job_status not null,
  to_status   job_status not null,
  primary key (from_status, to_status)
);

insert into allowed_transitions (from_status, to_status) values
  ('queued',         'tts_pending'),
  ('tts_pending',    'tts_done'),
  ('tts_done',       'render_pending'),
  ('render_pending', 'rendered'),
  ('rendered',       'delivered'),
  ('queued',         'failed'), ('tts_pending', 'failed'), ('tts_done', 'failed'),
  ('render_pending', 'failed'), ('rendered', 'failed'),
  ('queued',         'cancelled'), ('tts_pending', 'cancelled'), ('tts_done', 'cancelled'),
  ('render_pending', 'cancelled'), ('rendered', 'cancelled'), ('failed', 'cancelled')
on conflict do nothing;
-- failed -> <failed_stage> (retry) is checked inside transition_job().

-- Atomic compare-and-set transition. Raises if the job is not in p_expected
-- (someone else moved it) or the edge is not allowed.
create or replace function transition_job(
  p_job_id   uuid,
  p_expected job_status,
  p_to       job_status,
  p_actor    text,
  p_reason   text default null
) returns jobs
language plpgsql as $$
declare
  j jobs;
  ok boolean;
begin
  select * into j from jobs where id = p_job_id for update;
  if not found then
    raise exception 'job % not found', p_job_id using errcode = 'P0002';
  end if;
  if j.status <> p_expected then
    raise exception 'job % is %, expected %', p_job_id, j.status, p_expected using errcode = 'P0001';
  end if;

  if p_expected = 'failed' and p_to <> 'cancelled' then
    ok := (p_to = j.failed_stage);
  else
    select exists (select 1 from allowed_transitions
                   where from_status = p_expected and to_status = p_to) into ok;
  end if;
  if not ok then
    raise exception 'transition % -> % is not allowed', p_expected, p_to using errcode = 'P0001';
  end if;

  update jobs set
    status            = p_to,
    failed_stage      = case when p_to = 'failed' then p_expected
                             when p_expected = 'failed' then null
                             else failed_stage end,
    last_error        = case when p_to = 'failed' then p_reason
                             when p_expected = 'failed' then null
                             else last_error end,
    attempt           = case when p_expected = 'failed' and p_to <> 'cancelled' then attempt + 1 else attempt end,
    updated_at        = now(),
    status_changed_at = now()
  where id = p_job_id
  returning * into j;

  insert into job_events (job_id, from_status, to_status, actor, reason)
  values (p_job_id, p_expected, p_to, p_actor, p_reason);

  return j;
end $$;

-- Supabase exposes the public schema over its REST API to anyone holding the
-- (public) anon key. RLS with no policies closes that door; the MCP server
-- and workers connect as the postgres role, which bypasses RLS.
alter table jobs                enable row level security;
alter table job_events          enable row level security;
alter table assets              enable row level security;
alter table generation_calls    enable row level security;
alter table mcp_requests        enable row level security;
alter table allowed_transitions enable row level security;

-- Belt and braces: Supabase also exposes functions over RPC. Only the
-- server-side roles should be able to call transition_job().
revoke execute on function transition_job(uuid, job_status, job_status, text, text) from public;
do $$
declare r text;
begin
  foreach r in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke all on all tables in schema public from %I', r);
      execute format('revoke execute on function transition_job(uuid, job_status, job_status, text, text) from %I', r);
    end if;
  end loop;
end $$;
