PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,
    started_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    turn_no INTEGER NOT NULL,
    attacker_prompt TEXT,
    target_reply TEXT,
    tool_called TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS evals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    success INTEGER NOT NULL,
    reason TEXT,
    owasp_category TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE INDEX IF NOT EXISTS idx_turns_run ON turns(run_id);
CREATE INDEX IF NOT EXISTS idx_evals_run ON evals(run_id);
