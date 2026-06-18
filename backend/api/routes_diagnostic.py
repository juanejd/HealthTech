from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

import api.routes_dispense as dispense
from modules import servo_controller
from modules import sensor_manager
from modules.sensor_manager import HX711Error

router = APIRouter()


def _reject_if_busy() -> None:
    if dispense.is_busy:
        raise HTTPException(
            status_code=409,
            detail={"status": "busy", "detail": "dispense_active"},
        )


@router.post("/step")
async def step():
    _reject_if_busy()
    await run_in_threadpool(servo_controller.step_one_compartment)
    return {"status": "ok", "position": servo_controller.get_position()}


@router.post("/home")
async def home():
    _reject_if_busy()
    await run_in_threadpool(servo_controller.set_home)
    return {"status": "ok", "position": 0}


@router.get("/weight")
async def weight():
    try:
        weight_g = await run_in_threadpool(sensor_manager.read_weight)
        calibrated = sensor_manager.is_calibrated()
        return {"status": "ok", "weight_g": weight_g, "calibrated": calibrated}
    except HX711Error:
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "detail": "sensor_unavailable"},
        )


@router.post("/tare")
async def tare():
    # Never tare mid-dispense: the dispense confirmation reads a baseline and
    # watches for a weight drop. Re-zeroing while that runs would corrupt it.
    _reject_if_busy()
    await run_in_threadpool(sensor_manager.tare)
    try:
        weight_g = await run_in_threadpool(sensor_manager.read_weight)
        calibrated = sensor_manager.is_calibrated()
        return {"status": "ok", "weight_g": weight_g, "calibrated": calibrated}
    except HX711Error:
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "detail": "sensor_unavailable"},
        )
