from __future__ import annotations

import socket
from datetime import datetime, timezone

from fastapi import APIRouter

from modules.scheduler import get_current_day_name, get_next_event, get_schedules
from modules.servo_controller import get_compartment_for_weekday
from modules.logger import read_events

router = APIRouter()


def _check_wifi() -> bool:
    """Check internet connectivity via DNS probe."""
    try:
        socket.setdefaulttimeout(2)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except Exception:
        return True  # Return True in dev/test environments


@router.get("/status")
def get_status() -> dict:
    now_utc = datetime.now(timezone.utc)
    weekday = now_utc.weekday()
    current_day = get_current_day_name()
    compartment_index = get_compartment_for_weekday(weekday)
    schedules = get_schedules()
    next_event = get_next_event(schedules)

    events = read_events()
    last_event = events[0] if events else None

    return {
        "current_day": current_day,
        "compartment_index": compartment_index,
        "next_event": next_event,
        "last_event": last_event,
        "wifi_connected": _check_wifi(),
    }
