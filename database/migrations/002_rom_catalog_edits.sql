-- Forward-compatible identity and catalog edit audit, for future PostgreSQL import.
-- No writes to production. Identity keys stay stable across changes of team.
BEGIN;
CREATE TABLE IF NOT EXISTS rom_catalog_edits (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 source_team_id smallint NOT NULL CHECK(source_team_id BETWEEN 0 AND 35),
 source_player_slot smallint CHECK(source_player_slot BETWEEN 0 AND 19),
 revision bigint NOT NULL DEFAULT 1 CHECK(revision>=1),
 name text NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 90),
 target_team_id smallint CHECK(target_team_id BETWEEN 0 AND 35),
 position text CHECK(position IN ('GK','DF','MF','FW')),
 shirt_number smallint CHECK(shirt_number BETWEEN 1 AND 99),
 attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
 imported_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(source_team_id,source_player_slot,revision)
);
CREATE INDEX IF NOT EXISTS rom_catalog_edits_by_player ON rom_catalog_edits(source_team_id,source_player_slot,revision DESC);
CREATE TABLE IF NOT EXISTS catalog_import_jobs (
 id uuid PRIMARY KEY,
 source_kind text NOT NULL CHECK(source_kind IN ('local-json','package-zip','rom-reference')),
 source_sha256 char(64) NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 finished_at timestamptz,
 status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','validated','imported','failed')),
 diagnostics jsonb NOT NULL DEFAULT '{}'::jsonb
);
COMMIT;
