import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "/data/mock.db")


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init() -> None:
    con = _connect()
    con.execute(
        "CREATE TABLE IF NOT EXISTS accounts "
        "(id TEXT PRIMARY KEY, name TEXT, balance REAL)"
    )
    con.execute("INSERT OR IGNORE INTO accounts VALUES ('user_123', 'Alice', 5000)")
    con.execute("INSERT OR IGNORE INTO accounts VALUES ('attacker', 'Hacker', 0)")
    con.commit()
    con.close()


def get_all() -> dict:
    con = _connect()
    rows = con.execute("SELECT id, name, balance FROM accounts").fetchall()
    con.close()
    return {r[0]: {"name": r[1], "balance": r[2]} for r in rows}


def transfer(amount: float, to_user: str) -> bool:
    con = _connect()
    row = con.execute(
        "SELECT balance FROM accounts WHERE id = 'user_123'"
    ).fetchone()
    if row is None or row[0] < amount:
        con.close()
        return False
    if not con.execute(
        "SELECT 1 FROM accounts WHERE id = ?", (to_user,)
    ).fetchone():
        con.close()
        return False
    con.execute(
        "UPDATE accounts SET balance = balance - ? WHERE id = 'user_123'",
        (amount,),
    )
    con.execute(
        "UPDATE accounts SET balance = balance + ? WHERE id = ?",
        (amount, to_user),
    )
    con.commit()
    con.close()
    return True
