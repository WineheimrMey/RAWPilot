from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from .models import ProcessResult
from .settings import config_dir


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class HistoryItem(BaseModel):
    source: str
    status: str
    preview_path: str = ""
    suggested_style: str = ""
    final_prompt: str = ""
    diagnosis: dict = Field(default_factory=dict)
    plan: dict = Field(default_factory=dict)
    xmp_path: str = ""
    rendered_path: str = ""
    quality_note: str = ""
    error: str = ""


class ProjectRecord(BaseModel):
    id: str
    created_at: str
    updated_at: str
    output_dir: str
    title: str
    items: list[HistoryItem] = Field(default_factory=list)


class HistoryStore:
    """Local project ledger. It stores metadata and paths, never RAW bytes."""

    def __init__(self, path: Path | None = None):
        self.path = path or config_dir() / "history.json"

    def load(self) -> list[ProjectRecord]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return [ProjectRecord.model_validate(item) for item in payload.get("projects", [])]
        except (OSError, ValueError, TypeError):
            return []

    def begin(
        self,
        output_dir: Path,
        files: list[Path],
        title: str | None = None,
    ) -> ProjectRecord:
        stamp = _now()
        project_title = title or (
            files[0].stem
            if len(files) == 1
            else f"{files[0].stem} 等 {len(files)} 张"
        )
        project = ProjectRecord(
            id=uuid4().hex,
            created_at=stamp,
            updated_at=stamp,
            output_dir=str(output_dir),
            title=project_title,
        )
        projects = self.load()
        projects.insert(0, project)
        self._save(projects)
        return project

    def record(self, project_id: str, result: ProcessResult, final_prompt: str) -> None:
        projects = self.load()
        for project in projects:
            if project.id != project_id:
                continue
            item = HistoryItem(
                source=str(result.source),
                status=result.status,
                preview_path=str(result.preview_path or ""),
                suggested_style=result.suggested_style,
                final_prompt=final_prompt,
                diagnosis=result.diagnosis.model_dump(mode="json") if result.diagnosis else {},
                plan=result.plan.model_dump(mode="json") if result.plan else {},
                xmp_path=str(result.xmp_path or ""),
                rendered_path=str(result.rendered_path or ""),
                quality_note=result.quality_note,
                error=result.error,
            )
            project.items = [old for old in project.items if old.source != item.source]
            project.items.append(item)
            project.updated_at = _now()
            break
        self._save(projects)

    def delete(self, project_id: str) -> None:
        self._save([project for project in self.load() if project.id != project_id])

    def _save(self, projects: list[ProjectRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "projects": [item.model_dump(mode="json") for item in projects[:200]],
        }
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)
