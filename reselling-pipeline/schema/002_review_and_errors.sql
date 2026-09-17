-- Applied to Supabase project jaylee-reselling-pipeline (ref plbsnlmhzcwebbafqvuj).
-- Checked in here for review/history; the live schema was applied via the
-- Supabase migration API, not by running this file directly.

-- Supports self-correction in the pipeline:
--   needs_review  -- set by the ETL step when a CSV row is ambiguous/incomplete
--                     but not rejected outright (e.g. price parsed, but no
--                     images). Never pushed to Shopify until cleared.
--   notes         -- free text explaining why needs_review was set, or any
--                     other human-facing annotation.
--   error_message -- set by the Shopify push step when a row fails after
--                     retries, so failures are visible in Supabase instead of
--                     only in script stdout, and can be selectively re-queued.
alter table products
  add column needs_review boolean not null default false,
  add column notes text,
  add column error_message text;

alter table products
  drop constraint products_status_check,
  add constraint products_status_check check (status in ('staged','ready','pushed','sold','archived','error'));
