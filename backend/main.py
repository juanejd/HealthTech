from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_status import router as status_router
from api.routes_schedules import router as schedules_router
from api.routes_logs import router as logs_router
from api.routes_dispense import router as dispense_router
from api.routes_diagnostic import router as diagnostic_router
from api.websocket import router as ws_router
from modules.scheduler import reload_schedules
from modules import auto_dispenser


@asynccontextmanager
async def lifespan(app: FastAPI):
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    reload_schedules()
    auto_dispenser.start(asyncio.get_running_loop())
    try:
        yield
    finally:
        auto_dispenser.shutdown()


app = FastAPI(title="HealthTech API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status_router, prefix="/api")
app.include_router(schedules_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(dispense_router, prefix="/api")
app.include_router(diagnostic_router, prefix="/api/diagnostic")
app.include_router(ws_router)
