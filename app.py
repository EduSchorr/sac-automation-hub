from fastapi import FastAPI, HTTPException

from config import get_project_by_id
from core.metrics_db import get_stats
from core.process_manager import manager
from core.scheduler import scheduler, list_schedules, create_schedule

app = FastAPI(title="SAC Automation Hub", version="portfolio")

@app.on_event("startup")
def startup():
    scheduler.start()

@app.on_event("shutdown")
def shutdown():
    scheduler.stop()

@app.get("/api/health")
def health():
    return {"ok": True, "portfolio": True}

@app.get("/api/projects")
def projects():
    return manager.all_projects()

@app.post("/api/projects/{project_id}/start")
def start(project_id: str):
    if not get_project_by_id(project_id):
        raise HTTPException(status_code=404, detail="Project not found.")
    return manager.start(project_id)

@app.post("/api/projects/{project_id}/stop")
def stop(project_id: str):
    if not get_project_by_id(project_id):
        raise HTTPException(status_code=404, detail="Project not found.")
    return manager.stop(project_id)

@app.get("/api/metrics")
def metrics():
    return get_stats()

@app.get("/api/schedules")
def schedules():
    return list_schedules()

@app.post("/api/schedules")
def schedule(payload: dict):
    try:
        schedule_id = create_schedule(
            str(payload["name"]),
            str(payload["project_id"]),
            str(payload["action"]),
            str(payload["run_time"]),
            bool(payload.get("enabled", True)),
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"id": schedule_id}
