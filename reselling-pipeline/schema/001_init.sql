-- Applied to Supabase project jaylee-reselling-pipeline (ref plbsnlmhzcwebbafqvuj).
-- Checked in here for review/history; the live schema was applied via the
-- Supabase migration API, not by running this file directly.

create table products (
  sku text primary key,
  poshmark_id text unique,
  title text not null,
  description text,
  brand text,
  category text,
  price numeric(10,2) not null,
  compare_at_price numeric(10,2),
  condition text,
  size text,
  quantity int not null default 1,
  status text not null default 'staged' check (status in ('staged','ready','pushed','sold','archived')),
  source text not null default 'poshmark',
  shopify_product_id text,
  synced_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table product_images (
  id bigint generated always as identity primary key,
  sku text not null references products(sku) on delete cascade,
  drive_file_id text,
  url text not null,
  position int not null default 0,
  created_at timestamptz not null default now(),
  unique (sku, position)
);

create index on product_images (sku);

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger products_set_updated_at
before update on products
for each row execute function set_updated_at();
