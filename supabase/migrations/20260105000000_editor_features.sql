-- Migration: Add editor features to clips table
-- Created: 2026-01-05
-- Purpose: Add trim points, audio URL, voice ID, and text overlays table

-- Add trim_start and trim_end columns to clips for non-destructive trimming
do $$ 
begin 
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'trim_start') then
    alter table clips add column trim_start float default 0;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'trim_end') then
    alter table clips add column trim_end float default null;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'audio_url') then
    alter table clips add column audio_url text default null;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'voice_id') then
    alter table clips add column voice_id text default null;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'narration') then
    alter table clips add column narration text default null;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'captions') then
    alter table clips add column captions text default null;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'overlay') then
    alter table clips add column overlay jsonb default null;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'order_index') then
    alter table clips add column order_index integer default 0;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'title') then
    alter table clips add column title text default '';
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'duration') then
    alter table clips add column duration text default '00:00';
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'thumbnail_url') then
    alter table clips add column thumbnail_url text default null;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'feature_id') then
    alter table clips add column feature_id text default '';
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'created_at') then
    alter table clips add column created_at timestamp with time zone default now();
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'updated_at') then
    alter table clips add column updated_at timestamp with time zone default now();
  end if;
  -- Visual effects columns
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'click_effect') then
    alter table clips add column click_effect text default 'none';
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'zoom_effect') then
    alter table clips add column zoom_effect text default 'none';
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'clips' and column_name = 'click_events') then
    alter table clips add column click_events jsonb default null;
  end if;
end $$;

-- Add missing columns to demos table
do $$ 
begin 
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'title') then
    alter table demos add column title text default '';
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'description') then
    alter table demos add column description text default '';
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'repo_url') then
    alter table demos add column repo_url text default '';
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'video_url') then
    alter table demos add column video_url text default null;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'updated_at') then
    alter table demos add column updated_at timestamp with time zone default now();
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'brand_color') then
    alter table demos add column brand_color text default '#7c3aed';
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'export_format') then
    alter table demos add column export_format text default 'mp4';
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'export_resolution') then
    alter table demos add column export_resolution text default '1080p';
  end if;
  -- Intro/Outro tracking
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'has_intro') then
    alter table demos add column has_intro boolean default false;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'has_outro') then
    alter table demos add column has_outro boolean default false;
  end if;
end $$;

-- Create text_overlays table for more complex overlay management
create table if not exists text_overlays (
    id uuid primary key default gen_random_uuid(),
    clip_id uuid references clips(id) on delete cascade,
    text text not null,
    position_x float default 50,
    position_y float default 90,
    font_size integer default 24,
    font_color text default '#ffffff',
    background_color text default 'rgba(0,0,0,0.5)',
    animation text default 'fade',
    start_time float default 0,
    end_time float default null,
    created_at timestamp with time zone default now()
);

-- Create transitions table for clip transitions
create table if not exists transitions (
    id uuid primary key default gen_random_uuid(),
    demo_id uuid references demos(id) on delete cascade,
    from_clip_id uuid references clips(id) on delete cascade,
    to_clip_id uuid references clips(id) on delete cascade,
    transition_type text default 'dissolve',
    duration float default 0.5,
    created_at timestamp with time zone default now()
);

-- Create indexes for performance
create index if not exists idx_clips_demo_id on clips(demo_id);
create index if not exists idx_clips_order_index on clips(demo_id, order_index);
create index if not exists idx_text_overlays_clip_id on text_overlays(clip_id);
create index if not exists idx_transitions_demo_id on transitions(demo_id);

-- Add additional demo columns for export options
do $$ 
begin 
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'background_music') then
    alter table demos add column background_music text default null;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'music_volume') then
    alter table demos add column music_volume float default 0.15;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'aspect_ratio') then
    alter table demos add column aspect_ratio text default '16:9';
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'watermark') then
    alter table demos add column watermark text default null;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'enable_transitions') then
    alter table demos add column enable_transitions boolean default false;
  end if;
  if not exists (select 1 from information_schema.columns where table_name = 'demos' and column_name = 'transition_type') then
    alter table demos add column transition_type text default 'dissolve';
  end if;
end $$;

-- Create export_jobs table for tracking export progress
create table if not exists export_jobs (
    id uuid primary key default gen_random_uuid(),
    demo_id uuid references demos(id) on delete cascade,
    status text default 'queued',
    progress integer default 0,
    step text default '',
    error text default null,
    result_url text default null,
    options jsonb default null,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now(),
    completed_at timestamp with time zone default null
);

-- Create index for export_jobs
create index if not exists idx_export_jobs_demo_id on export_jobs(demo_id);
create index if not exists idx_export_jobs_status on export_jobs(status);

