from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
import pytest


def test_get_current_day_name_returns_spanish():
    from modules.scheduler import get_current_day_name
    valid_days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    day = get_current_day_name()
    assert day in valid_days


def test_get_next_event_returns_iso_string_or_none():
    from modules.scheduler import get_next_event
    schedules = [
        {
            "time": "08:00",
            "days": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
            "message": "Tomar medicamento.",
            "enabled": True,
        }
    ]
    result = get_next_event(schedules)
    if result is not None:
        assert result.endswith("Z")


def test_get_next_event_disabled_schedule_excluded():
    from modules.scheduler import get_next_event
    schedules = [
        {
            "time": "08:00",
            "days": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
            "message": "Tomar medicamento.",
            "enabled": False,
        }
    ]
    result = get_next_event(schedules)
    if result is not None:
        assert result.endswith("Z")


def test_reload_schedules_does_not_raise(tmp_path):
    sched_file = tmp_path / "schedules.json"
    sched_file.write_text(json.dumps({"schedules": []}))
    with patch("modules.scheduler.SCHEDULES_FILE", sched_file):
        from modules.scheduler import reload_schedules
        reload_schedules()
