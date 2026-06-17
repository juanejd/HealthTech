from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks

from modules.logger import log_event
from modules.servo_controller import get_compartment_for_weekday, move_to_compartment
from modules.sensor_manager import wait_for_extraction
from modules.tts_engine import speak
from modules.telegram_bot import send_notification
from modules.fault_tolerance import enqueue
from modules.scheduler import get_current_day_name
from api.websocket import manager

router = APIRouter()


async def _broadcast_status(result: dict) -> None:
    """Broadcast dispense result to all WebSocket clients."""
    try:
        await manager.broadcast(result)
    except Exception:
        pass


@router.post("/dispense")
async def post_dispense(background_tasks: BackgroundTasks) -> dict:
    now_utc = datetime.now(timezone.utc)
    weekday = now_utc.weekday()
    day_name = get_current_day_name()
    compartment_index = get_compartment_for_weekday(weekday)
    timestamp = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    speak("Es hora de tomar su medicamento.")
    move_to_compartment(compartment_index)
    extraction_detected = wait_for_extraction()

    status = "OK" if extraction_detected else "FAIL"

    log_event("dispense", status, extraction_detected, day_name, compartment_index)

    result = {
        "status": status,
        "extraction_detected": extraction_detected,
        "timestamp": timestamp,
    }

    notification = {**result, "day": day_name, "compartment_index": compartment_index}
    enqueue(notification)
    send_notification(notification)

    background_tasks.add_task(_broadcast_status, result)

    return result
