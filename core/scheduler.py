import sqlite3
import threading
from datetime import datetime

from config import get_project_by_id
from core.metrics_db import DB_PATH
from core.process_manager import manager

def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_schedule_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                project_id TEXT NOT NULL,
                action TEXT NOT NULL CHECK(action IN ('start','stop')),
                run_time TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                last_run_date TEXT,
                created_at TEXT NOT NULL
            )
        """)

def list_schedules():
    init_schedule_db()
    with _connect() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM scheduled_tasks ORDER BY run_time,id")]

def create_schedule(name, project_id, action, run_time, enabled=True):
    if not get_project_by_id(project_id):
        raise ValueError("Unknown project.")
    init_schedule_db()
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO scheduled_tasks(name,project_id,action,run_time,enabled,created_at) VALUES(?,?,?,?,?,?)",
            (name.strip(), project_id, action, run_time, int(enabled), datetime.now().isoformat(timespec="seconds")),
        )
        return cursor.lastrowid

def _claim(schedule_id, today):
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM scheduled_tasks WHERE id=? AND enabled=1 AND (last_run_date IS NULL OR last_run_date<>?)",
            (schedule_id, today),
        ).fetchone()
        if not row:
            return None
        conn.execute("UPDATE scheduled_tasks SET last_run_date=? WHERE id=?", (today, schedule_id))
        return dict(row)

class DailyScheduler:
    def __init__(self, interval_seconds=10):
        self.interval_seconds = interval_seconds
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        init_schedule_db()
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True, name="automation-hub-scheduler")
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def _run(self):
        while not self.stop_event.is_set():
            now = datetime.now()
            for item in list_schedules():
                if item["enabled"] and item["run_time"] == now.strftime("%H:%M"):
                    task = _claim(item["id"], now.date().isoformat())
                    if task:
                        manager.start(task["project_id"]) if task["action"] == "start" else manager.stop(task["project_id"])
            self.stop_event.wait(self.interval_seconds)

scheduler = DailyScheduler()
