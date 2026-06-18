from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

SCHEDULES_FILE: Path = Path(__file__).parent.parent / "config" / "schedules.json"

_SPANISH_DAYS = [
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
]

_loaded_schedules: Optional[List[dict]] = None


def get_current_day_name() -> str:
    """Returns Spanish day name for today in UTC."""
    weekday = datetime.now(timezone.utc).weekday()
    return _SPANISH_DAYS[weekday]


def reload_schedules() -> None:
    """Re-read schedules from disk. Uses the current SCHEDULES_FILE value."""
    global _loaded_schedules
    try:
        data = json.loads(SCHEDULES_FILE.read_text(encoding="utf-8"))
        _loaded_schedules = data.get("schedules", [])
    except Exception as exc:
        logger.error("Failed to load schedules: %s", exc)
        _loaded_schedules = []


def get_schedules() -> List[dict]:
    """Return currently loaded schedules, loading from disk if needed."""
    if _loaded_schedules is None:
        reload_schedules()
    return _loaded_schedules or []


def get_next_event(schedules: List[dict]) -> Optional[str]:
    """
    Returns ISO-8601 UTC string for the next scheduled event.
    Looks ahead up to 7 days.
    """
    now = datetime.now(timezone.utc)
    enabled = [s for s in schedules if s.get("enabled", True)]
    if not enabled:
        return None

    best: Optional[datetime] = None

    for days_ahead in range(8):
        target_date = now + timedelta(days=days_ahead)
        target_day_name = _SPANISH_DAYS[target_date.weekday()]

        for schedule in enabled:
            if target_day_name not in schedule.get("days", []):
                continue
            try:
                hour, minute = map(int, schedule["time"].split(":"))
            except (KeyError, ValueError):
                continue
            candidate = target_date.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            if candidate <= now:
                continue
            if best is None or candidate < best:
                best = candidate

        if best is not None:
            break

    if best is None:
        return None
    return best.strftime("%Y-%m-%dT%H:%M:%SZ")
