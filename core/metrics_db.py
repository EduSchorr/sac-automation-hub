import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "hub_database.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                project_title TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                duration_seconds REAL,
                exit_code INTEGER,
                details TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_settings (
                project_id TEXT PRIMARY KEY,
                is_visible INTEGER DEFAULT 1,
                is_favorite INTEGER DEFAULT 0
            )
        """)

def log_execution_start(project_id: str, title: str, action: str = "START") -> int:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "INSERT INTO executions(project_id,project_title,action,status,started_at) VALUES(?,?,?,'RUNNING',?)",
            (project_id, title, action, datetime.now().isoformat(timespec="seconds")),
        )
        return cursor.lastrowid

def log_execution_end(exec_id: int, status: str, exit_code=None, details=None):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT started_at FROM executions WHERE id=?", (exec_id,)).fetchone()
        ended = datetime.now()
        duration = None
        if row:
            duration = round((ended - datetime.fromisoformat(row[0])).total_seconds(), 1)
        conn.execute(
            "UPDATE executions SET status=?,ended_at=?,duration_seconds=?,exit_code=?,details=? WHERE id=?",
            (status, ended.isoformat(timespec="seconds"), duration, exit_code, details, exec_id),
        )

def get_stats():
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM executions").fetchone()[0]
        success = conn.execute("SELECT COUNT(*) FROM executions WHERE status='SUCCESS'").fetchone()[0]
        errors = conn.execute("SELECT COUNT(*) FROM executions WHERE status='ERROR'").fetchone()[0]
    return {"total_runs": total, "success_runs": success, "error_runs": errors}
