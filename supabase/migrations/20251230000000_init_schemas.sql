-- Create demos table if it doesn't exist
create table if not exists demos (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null,
  status text not null,
  created_at timestamp with time zone default now()
);

-- Ensure demos columns are not null
alter table demos alter column project_id set not null;
alter table demos alter column status set not null;

-- Create clips table if it doesn't exist
create table if not exists clips (
  id uuid primary key default gen_random_uuid(),
  demo_id uuid references demos(id),
  feature text,
  start_time float,
  end_time float,
  video_url text
);

-- Add missing columns to clips if they don't exist
do $$ 
begin 
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'feature') then
    alter table clips add column feature text;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'start_time') then
    alter table clips add column start_time float;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'end_time') then
    alter table clips add column end_time float;
  end if;
end $$;
