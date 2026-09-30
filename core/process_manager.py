import asyncio
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

import psutil

from config import PROJECTS, get_project_by_id
from core.metrics_db import log_execution_end, log_execution_start

class ProcessManager:
    def __init__(self):
        self.running = {}
        self.info = {}
        self.logs = {}
        self.subscribers = {}

    def status(self, project_id: str) -> str:
        process = self.running.get(project_id)
        if process is None:
            return "STOPPED"
        return "RUNNING" if process.poll() is None else "FINISHED"

    def all_projects(self):
        result = []
        for project in PROJECTS:
            result.append({
                **project,
                "status": self.status(project["id"]),
                "exists": Path(project["path"]).exists(),
                **self.info.get(project["id"], {}),
            })
        return result

    def _reader(self, project_id, stream, source):
        buffer = self.logs.setdefault(project_id, [])
        for line in iter(stream.readline, ""):
            if not line:
                break
            message = f"[{datetime.now():%H:%M:%S}] [{source}] {line.rstrip()}"
            buffer.append(message)
            del buffer[:-1000]
            for queue in list(self.subscribers.get(project_id, [])):
                try:
                    queue.put_nowait(message)
                except Exception:
                    pass

    def _monitor(self, project_id, process, exec_id):
        process.wait()
        log_execution_end(exec_id, "SUCCESS" if process.returncode == 0 else "ERROR", process.returncode)
        self.running.pop(project_id, None)

    def start(self, project_id: str):
        if self.status(project_id) == "RUNNING":
            return {"success": False, "message": "Project is already running."}
        project = get_project_by_id(project_id)
        if not project:
            return {"success": False, "message": "Project not found."}
        project_path = Path(project["path"])
        if not project_path.exists():
            return {"success": False, "message": "Project directory is not available in this environment."}

        command = list(project["command"])
        if command[0] == "python":
            command[0] = sys.executable

        exec_id = log_execution_start(project_id, project["title"])
        process = subprocess.Popen(
            command,
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        self.running[project_id] = process
        self.info[project_id] = {"pid": process.pid, "started_at": datetime.now().isoformat(timespec="seconds")}

        threading.Thread(target=self._reader, args=(project_id, process.stdout, "OUT"), daemon=True).start()
        threading.Thread(target=self._reader, args=(project_id, process.stderr, "ERR"), daemon=True).start()
        threading.Thread(target=self._monitor, args=(project_id, process, exec_id), daemon=True).start()

        return {"success": True, "pid": process.pid, "web_url": project.get("web_url")}

    def stop(self, project_id: str):
        process = self.running.get(project_id)
        if not process or process.poll() is not None:
            return {"success": False, "message": "Project is not running."}
        parent = psutil.Process(process.pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
        return {"success": True}

    def subscribe(self, project_id: str):
        queue = asyncio.Queue()
        self.subscribers.setdefault(project_id, []).append(queue)
        return queue

manager = ProcessManager()
