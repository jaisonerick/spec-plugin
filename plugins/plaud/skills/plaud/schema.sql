-- Plaud recordings catalog — sqlite schema.
-- The database is a git-ignored, rebuildable index. The source of truth is
-- catalog.jsonl; run `plaud_hub.py build` to (re)compile this DB from it.

CREATE TABLE IF NOT EXISTS recordings (
  id              TEXT PRIMARY KEY,   -- Plaud recording id (also the web.plaud.ai/file/<id> slug)
  filename        TEXT,               -- name shown in Plaud
  start_time      INTEGER,            -- epoch milliseconds (canonical timestamp)
  recorded_at     TEXT,               -- ISO local time in the configured timezone, derived from start_time
  duration_ms     INTEGER,
  duration_min    REAL,
  scene           INTEGER,            -- Plaud "scene" code
  url             TEXT,               -- https://web.plaud.ai/file/<id>

  -- state pulled from Plaud
  is_trans        INTEGER,            -- 0/1 — transcript exists in Plaud
  is_summary      INTEGER,            -- 0/1 — summary exists in Plaud
  tags            TEXT,               -- JSON array of tag names

  -- curation (maintained in catalog.jsonl, never overwritten by a refresh)
  project         TEXT,               -- free label for the project this belongs to
  path            TEXT,               -- where it was filed, relative to the repository root
  repo            TEXT,               -- another repo it relates to, as owner/repo
  status          TEXT,               -- pending | transcribed | filed | excluded
  transcript_path TEXT,               -- local copy of the transcript, relative to the repository root
  summary_path    TEXT,               -- local copy of the summary, relative to the repository root
  excluded_reason TEXT,               -- why it is out of scope for this repository
  notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_recordings_status  ON recordings(status);
CREATE INDEX IF NOT EXISTS idx_recordings_project ON recordings(project);
CREATE INDEX IF NOT EXISTS idx_recordings_trans   ON recordings(is_trans);
CREATE INDEX IF NOT EXISTS idx_recordings_start   ON recordings(start_time);

-- Convenience view: recordings whose transcription has not been activated yet.
CREATE VIEW IF NOT EXISTS pending_transcription AS
  SELECT id, recorded_at, duration_min, filename, url
  FROM recordings
  WHERE is_trans = 0 AND status = 'pending'
  ORDER BY start_time DESC;

-- Convenience view: transcribed but not yet filed into a project.
CREATE VIEW IF NOT EXISTS unfiled AS
  SELECT id, recorded_at, duration_min, filename, tags, url
  FROM recordings
  WHERE is_trans = 1 AND status = 'transcribed'
  ORDER BY start_time DESC;
