from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool

from modules import servo_controller
from modules import sensor_manager

router = APIRouter()


@router.post("/step")
async def step():
    await run_in_threadpool(servo_controller.step_one_compartment)
    return {"status": "ok", "message": "stepped"}


@router.post("/home")
async def home():
    await run_in_threadpool(servo_controller.set_home)
    return {"status": "ok", "message": "homed"}


@router.get("/weight")
async def weight():
    val = await run_in_threadpool(sensor_manager.read_weight)
    return {"status": "ok", "weight": val}
