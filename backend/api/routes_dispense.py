from __future__ import annotations

from datetime import datetime, timezone

from starlette.concurrency import run_in_threadpool
from fastapi import APIRouter, BackgroundTasks

from modules.logger import log_event
from modules.servo_controller import get_compartment_for_weekday, advance_to_compartment
from modules.sensor_manager import wait_for_dispense_confirmation, tare, HX711Error
from modules.fault_tolerance import enqueue
from modules.scheduler import get_current_day_name
from api.websocket import manager

router = APIRouter()

is_busy = False


async def _broadcast_status(result: dict) -> None:
    """Broadcast dispense result to all WebSocket clients."""
    try:
        await manager.broadcast(result)
    except Exception:
        pass


def _run_dispense_hardware(compartment_index: int) -> bool:
    """Synchronous helper to run the hardware steps for dispense."""
    advance_to_compartment(compartment_index)
    tare()
    return wait_for_dispense_confirmation()


@router.post("/dispense")
async def post_dispense(background_tasks: BackgroundTasks) -> dict:
    global is_busy
    is_busy = True

    try:
        now_utc = datetime.now(timezone.utc)
        weekday = now_utc.weekday()
        day_name = get_current_day_name()
        compartment_index = get_compartment_for_weekday(weekday)
        timestamp = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            dispense_confirmed = await run_in_threadpool(
                _run_dispense_hardware, compartment_index
            )
            status = "OK" if dispense_confirmed else "FAIL"
        except HX711Error:
            dispense_confirmed = False
            status = "FAIL"

        log_event("dispense", status, dispense_confirmed, day_name, compartment_index)

        result = {
            "status": status,
            "extraction_detected": dispense_confirmed,
            "timestamp": timestamp,
        }

        notification = {
            **result,
            "day": day_name,
            "compartment_index": compartment_index,
        }
        enqueue(notification)

        background_tasks.add_task(_broadcast_status, result)

        return result
    finally:
        is_busy = False
