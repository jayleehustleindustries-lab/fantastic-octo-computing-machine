-- Applied to Supabase project jaylee-reselling-pipeline (ref plbsnlmhzcwebbafqvuj).
-- Checked in here for review/history; the live schema was applied via the
-- Supabase migration API, not by running this file directly.

-- "Where the item is currently located" -- the physical bin/rack code from
-- the EHC inventory sheet's "Storage Location" column (e.g. "A1", "A4").
alter table products add column storage_location text;
