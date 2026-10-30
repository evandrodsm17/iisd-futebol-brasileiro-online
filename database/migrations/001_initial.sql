-- PostgreSQL foundation, not deployed by this PR.
-- Application-owned IDs are stable UUIDs; ROM source references are optional.
BEGIN;
CREATE TABLE IF NOT EXISTS clubs (
 id uuid PRIMARY KEY,
 slug text NOT NULL UNIQUE,
 name text NOT NULL CHECK (char_length(trim(name)) BETWEEN 1 AND 90),
 city text,
 country text,
 crest_path text,
 source_rom_team_id smallint UNIQUE CHECK (source_rom_team_id BETWEEN 0 AND 35),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS stadiums (
 id uuid PRIMARY KEY,
 name text NOT NULL,
 city text,
 layout_id smallint CHECK(layout_id BETWEEN 0 AND 7),
 image_path text,
 created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE clubs ADD COLUMN IF NOT EXISTS stadium_id uuid REFERENCES stadiums(id) ON DELETE SET NULL;
CREATE TABLE IF NOT EXISTS players (
 id uuid PRIMARY KEY,
 name text NOT NULL CHECK(char_length(trim(name)) BETWEEN 1 AND 90),
 position text NOT NULL CHECK(position IN ('GK','DF','MF','FW')),
 attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
 source_rom_team_id smallint CHECK(source_rom_team_id BETWEEN 0 AND 35),
 source_rom_slot smallint CHECK(source_rom_slot BETWEEN 0 AND 19),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(source_rom_team_id,source_rom_slot)
);
CREATE TABLE IF NOT EXISTS club_memberships (
 id uuid PRIMARY KEY,
 club_id uuid NOT NULL REFERENCES clubs(id),
 player_id uuid NOT NULL REFERENCES players(id),
 start_date date NOT NULL,
 end_date date,
 shirt_number smallint CHECK(shirt_number BETWEEN 1 AND 99),
 CHECK(end_date IS NULL OR end_date>=start_date),
 UNIQUE(club_id,player_id,start_date)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_club_per_player ON club_memberships(player_id) WHERE end_date IS NULL;
CREATE TABLE IF NOT EXISTS kits (
 id uuid PRIMARY KEY,
 club_id uuid NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
 kind text NOT NULL CHECK(kind IN ('home','away','third','goalkeeper')),
 colours jsonb NOT NULL,
 pattern text NOT NULL DEFAULT 'solid',
 UNIQUE(club_id,kind)
);
CREATE TABLE IF NOT EXISTS content_packages (
 id text PRIMARY KEY,
 revision integer NOT NULL CHECK(revision>0),
 schema_version integer NOT NULL,
 content_sha256 char(64) NOT NULL,
 payload jsonb NOT NULL,
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS competitions (
 id uuid PRIMARY KEY,
 name text NOT NULL,
 kind text NOT NULL CHECK(kind IN ('league','cup','continental')),
 rule_version text NOT NULL,
 rules jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS seasons (
 id uuid PRIMARY KEY,
 competition_id uuid NOT NULL REFERENCES competitions(id),
 label text NOT NULL,
 starts_on date,
 ends_on date,
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','active','finished')),
 CHECK(ends_on IS NULL OR starts_on IS NULL OR ends_on>=starts_on)
);
CREATE TABLE IF NOT EXISTS season_teams (
 season_id uuid NOT NULL REFERENCES seasons(id),
 club_id uuid NOT NULL REFERENCES clubs(id),
 PRIMARY KEY(season_id,club_id)
);
CREATE TABLE IF NOT EXISTS matches (
 id uuid PRIMARY KEY,
 season_id uuid REFERENCES seasons(id),
 home_club_id uuid NOT NULL REFERENCES clubs(id),
 away_club_id uuid NOT NULL REFERENCES clubs(id),
 kickoff_at timestamptz,
 status text NOT NULL DEFAULT 'scheduled' CHECK(status IN ('scheduled','live','finished','cancelled')),
 home_score smallint CHECK(home_score>=0),
 away_score smallint CHECK(away_score>=0),
 simulation_version text,
 CHECK(home_club_id<>away_club_id)
);
CREATE INDEX IF NOT EXISTS matches_season_time_idx ON matches(season_id,kickoff_at);
COMMIT;
