-- Create places table for Google Place API data
create table if not exists places (
  id uuid primary key default gen_random_uuid(),
  
  -- Google Place API fields
  place_id text unique not null,
  name text not null,
  formatted_address text,
  vicinity text,
  
  -- Location
  latitude double precision,
  longitude double precision,
  
  -- Additional Google data
  types text[],
  rating double precision,
  user_ratings_total integer,
  price_level integer,
  
  -- Business info
  phone_number text,
  website text,
  opening_hours jsonb,
  
  -- Custom attributes (for future extensions)
  custom_attributes jsonb default '{}'::jsonb,
  
  -- Metadata
  country text default 'ES',
  last_synced_at timestamp with time zone,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create index on place_id for fast lookups
create index if not exists idx_places_place_id on places(place_id);

-- Create index on country for filtering
create index if not exists idx_places_country on places(country);

-- Create index on types for category filtering
create index if not exists idx_places_types on places using gin(types);

-- Create updated_at trigger
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = timezone('utc'::text, now());
  return new;
end;
$$ language plpgsql;

create trigger update_places_updated_at
  before update on places
  for each row
  execute function update_updated_at_column();

-- ============================================================
-- User Plans Storage
-- ============================================================

create table if not exists user_plans (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  name text not null,
  description text,
  vibe text,
  total_duration integer,
  total_distance double precision,
  stops jsonb not null,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default timezone('utc'::text, now())
);

create index if not exists idx_user_plans_user_id on user_plans(user_id);
create index if not exists idx_user_plans_created_at on user_plans(created_at desc);
