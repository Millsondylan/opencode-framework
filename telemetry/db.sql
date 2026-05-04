-- Telemetry schema for opencode-framework.
-- Applied on top of the hook event tables that already exist in
-- .claude/hooks/logs/telemetry.sqlite: tool_events, prompt_events,
-- stop_events, subagent_events. This file defines the rollup tables,
-- indexes, and views consumed by telemetry/rollup.py and the dashboard.
-- Zero banned dashes. Uses ASCII hyphen only.

PRAGMA foreign_keys = ON;

-- One row per subagent invocation. Populated by the rollup when it walks
-- subagent_events and prompt_events, or by hooks that write directly.
CREATE TABLE IF NOT EXISTS agent_invocations (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                TEXT    NOT NULL,
    agent_name        TEXT    NOT NULL,
    stage_number      INTEGER,
    session_id        TEXT    NOT NULL,
    model             TEXT    NOT NULL,
    tokens_in         INTEGER NOT NULL DEFAULT 0,
    tokens_out        INTEGER NOT NULL DEFAULT 0,
    duration_ms       INTEGER NOT NULL DEFAULT 0,
    confidence_score  INTEGER,
    outcome           TEXT    NOT NULL DEFAULT 'unknown',
    error             TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_invocations_ts
    ON agent_invocations (ts);

CREATE INDEX IF NOT EXISTS idx_agent_invocations_agent_ts
    ON agent_invocations (agent_name, ts);

CREATE INDEX IF NOT EXISTS idx_agent_invocations_session
    ON agent_invocations (session_id);

-- One row per full pipeline run. Captures the envelope summary that
-- decide-agent closes with.
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        TEXT    NOT NULL,
    ts_start          TEXT    NOT NULL,
    ts_end            TEXT,
    run_number        INTEGER NOT NULL DEFAULT 1,
    total_runs        INTEGER NOT NULL DEFAULT 1,
    status            TEXT    NOT NULL DEFAULT 'running',
    mean_confidence   REAL,
    duration_ms       INTEGER,
    notes             TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_ts
    ON pipeline_runs (ts_start);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_session
    ON pipeline_runs (session_id);

-- One row per golden suite task outcome. Populated by eval/runner.py
-- and eval/scoreboard.py.
CREATE TABLE IF NOT EXISTS golden_results (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT    NOT NULL,
    task_id      TEXT    NOT NULL,
    category     TEXT    NOT NULL DEFAULT 'unknown',
    pass         INTEGER NOT NULL DEFAULT 0,
    latency_ms   INTEGER NOT NULL DEFAULT 0,
    tokens_total INTEGER NOT NULL DEFAULT 0,
    model        TEXT    NOT NULL DEFAULT 'unknown',
    notes        TEXT
);

CREATE INDEX IF NOT EXISTS idx_golden_results_ts
    ON golden_results (ts);

CREATE INDEX IF NOT EXISTS idx_golden_results_task
    ON golden_results (task_id, ts);

-- Daily rollup summary, written by telemetry/rollup.py --rollup.
CREATE TABLE IF NOT EXISTS daily_rollups (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    rollup_date       TEXT    NOT NULL UNIQUE,
    invocation_count  INTEGER NOT NULL DEFAULT 0,
    tokens_in_total   INTEGER NOT NULL DEFAULT 0,
    tokens_out_total  INTEGER NOT NULL DEFAULT 0,
    mean_confidence   REAL,
    opus_count        INTEGER NOT NULL DEFAULT 0,
    sonnet_count      INTEGER NOT NULL DEFAULT 0,
    error_count       INTEGER NOT NULL DEFAULT 0,
    p95_latency_ms    INTEGER,
    generated_at      TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_daily_rollups_date
    ON daily_rollups (rollup_date);

-- Anomaly ledger. Each anomaly emitted by rollup.detect_anomalies lands
-- here for audit, with a resolved flag for operator follow up.
CREATE TABLE IF NOT EXISTS anomaly_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT    NOT NULL,
    kind        TEXT    NOT NULL,
    severity    TEXT    NOT NULL DEFAULT 'warning',
    message     TEXT    NOT NULL,
    resolved    INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_anomaly_events_ts
    ON anomaly_events (ts);

-- Per agent aggregate view. Gives the dashboard a single table read
-- for its Agent Stats section.
CREATE VIEW IF NOT EXISTS agent_stats AS
SELECT
    agent_name,
    COUNT(*) AS invocation_count,
    AVG(CAST(confidence_score AS REAL))            AS mean_confidence,
    AVG(CAST(tokens_in  AS REAL) + CAST(tokens_out AS REAL)) AS mean_tokens,
    SUM(tokens_in)  AS tokens_in_total,
    SUM(tokens_out) AS tokens_out_total,
    SUM(CASE WHEN outcome = 'error' THEN 1 ELSE 0 END) AS error_count,
    MAX(ts) AS last_seen
FROM agent_invocations
GROUP BY agent_name;

-- Daily token spend view. Cost estimates use published public pricing
-- for Opus 4.7 and Sonnet 4.6. Adjust when pricing changes.
CREATE VIEW IF NOT EXISTS daily_cost AS
SELECT
    substr(ts, 1, 10) AS day,
    SUM(tokens_in)    AS tokens_in,
    SUM(tokens_out)   AS tokens_out,
    SUM(CASE WHEN model LIKE 'claude-opus%'   THEN tokens_out ELSE 0 END) AS opus_out,
    SUM(CASE WHEN model LIKE 'claude-sonnet%' THEN tokens_out ELSE 0 END) AS sonnet_out,
    ROUND(
        SUM(CASE WHEN model LIKE 'claude-opus%'   THEN tokens_out ELSE 0 END) * 75.0 / 1000000.0
      + SUM(CASE WHEN model LIKE 'claude-sonnet%' THEN tokens_out ELSE 0 END) * 15.0 / 1000000.0,
        4
    ) AS estimated_cost_usd
FROM agent_invocations
GROUP BY substr(ts, 1, 10);

-- Convenience view: recent pipeline runs with their rolled up
-- confidence and duration in one row.
CREATE VIEW IF NOT EXISTS recent_runs AS
SELECT
    id,
    session_id,
    ts_start,
    ts_end,
    run_number,
    total_runs,
    status,
    mean_confidence,
    duration_ms
FROM pipeline_runs
ORDER BY ts_start DESC;
