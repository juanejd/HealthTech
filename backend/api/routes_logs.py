from __future__ import annotations

from fastapi import APIRouter

from modules.logger import read_events

router = APIRouter()


@router.get("/logs")
def get_logs() -> dict:
    events = read_events()
    return {"events": events, "total": len(events)}
