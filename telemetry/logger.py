"""Thin SQLite writer for attack traces and evaluations."""

from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = os.environ.get("TELEMETRY_DB", "telemetry/aegis.db")
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode = WAL")
    return con


def init_db() -> None:
    schema = SCHEMA_PATH.read_text()
    con = _connect()
    con.executescript(schema)
    con.commit()
    con.close()


def new_run(target_id: str) -> str:
    run_id = uuid.uuid4().hex[:8]
    con = _connect()
    con.execute(
        "INSERT INTO runs (id, target_id, started_at) VALUES (?, ?, ?)",
        (run_id, target_id, _now()),
    )
    con.commit()
    con.close()
    return run_id


def log_turn(run_id: str, turn_no: int, prompt: str, reply: str, tool_called: str | None = None) -> None:
    con = _connect()
    con.execute(
        "INSERT INTO turns (run_id, turn_no, attacker_prompt, target_reply, tool_called, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (run_id, turn_no, prompt, reply, tool_called, _now()),
    )
    con.commit()
    con.close()


def log_eval(run_id: str, success: bool, reason: str, owasp_category: str) -> None:
    con = _connect()
    con.execute(
        "INSERT INTO evals (run_id, success, reason, owasp_category, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (run_id, int(success), reason, owasp_category, _now()),
    )
    con.commit()
    con.close()
