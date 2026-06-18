from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from modules.scheduler import reload_schedules

router = APIRouter()

SCHEDULES_FILE: Path = Path(__file__).parent.parent / "config" / "schedules.json"

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class ScheduleEntry(BaseModel):
    time: str
    days: List[str]
    message: str
    enabled: bool

    @field_validator("time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if not _TIME_RE.match(v):
            raise ValueError(
                f"Invalid time format: '{v}'. Expected HH:MM (00:00-23:59)."
            )
        return v


class SchedulesPayload(BaseModel):
    schedules: List[ScheduleEntry]


@router.get("/schedules")
def get_schedules_endpoint() -> dict:
    try:
        data = json.loads(SCHEDULES_FILE.read_text(encoding="utf-8"))
        return data
    except Exception:
        return {"schedules": []}


@router.put("/schedules")
def put_schedules(payload: SchedulesPayload) -> dict:
    data = payload.model_dump()
    SCHEDULES_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    reload_schedules()
    return data
