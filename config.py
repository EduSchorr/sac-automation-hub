import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUTOMATION_ROOT = Path(os.environ.get("AUTOMATION_PROJECTS_DIR", str(BASE_DIR.parent)))

PROJECTS = [
    {
        "id": "financial_automation",
        "title": "Financial Automation Center",
        "category": "Finance",
        "path": str(AUTOMATION_ROOT / "financial-automation-center"),
        "command": ["python", "app.py"],
        "launch_type": "web",
        "web_url": "http://127.0.0.1:8050",
    },
    {
        "id": "digital_service",
        "title": "Digital Service Center",
        "category": "Customer Service",
        "path": str(AUTOMATION_ROOT / "digital-service-center"),
        "command": ["python", "server.py"],
        "launch_type": "web",
        "web_url": "http://127.0.0.1:8000",
    },
    {
        "id": "pending_cases",
        "title": "Pending Cases Tracker",
        "category": "Operations",
        "path": str(AUTOMATION_ROOT / "pending-cases-tracker"),
        "command": ["python", "app.py"],
        "launch_type": "desktop",
    },
    {
        "id": "returns_verification",
        "title": "Returns Verification Center",
        "category": "Reverse Logistics",
        "path": str(AUTOMATION_ROOT / "returns-verification-center"),
        "command": ["python", "server.py"],
        "launch_type": "web",
        "web_url": "http://127.0.0.1:8051",
    },
]

def get_project_by_id(project_id: str):
    return next((project for project in PROJECTS if project["id"] == project_id), None)
