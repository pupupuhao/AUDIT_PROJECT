from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


def match_project(file: Any, projects: Iterable[Dict[str, Any]]) -> Optional[str]:
    filename = str(getattr(file, "filename", "") or getattr(file, "name", "") or "")
    for project in projects:
        project_key = str(project.get("project_key") or "")
        project_name = str(project.get("project_name") or "")
        if project_key and project_key in filename:
            return project_key
        if project_name and project_name in filename:
            return project_key or project_name
    return None

