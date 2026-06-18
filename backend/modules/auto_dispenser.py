"""
auto_dispenser.py — Cron-style automatic dispensing driven by config/schedules.json.

Bridges the configured reminder schedules to real dispense cycles. For every
enabled schedule entry (time + days), an APScheduler cron job is registered;
when it fires, a full dispense cycle runs (carousel → tare → weight-drop
confirmation), exactly as if POST /api/dispense had been called.

Design notes:
  - BackgroundScheduler (thread-based) is used instead of AsyncIOScheduler so
    job execution never depends on the FastAPI event loop being free, and the
    test suite can start/stop it without an async context.
  - Schedules are interpreted in UTC, matching scheduler.get_next_event and the
    timestamps written by logger.log_event.
  - When a job fires while a dispense is already in progress (is_busy), it is
    skipped — the carousel must never be re-driven mid-cycle.
  - The WebSocket broadcast is dispatched back onto the captured event loop via
    run_coroutine_threadsafe, since the job body runs in a scheduler thread.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import utc

from modules.scheduler import get_schedules

logger = logging.getLogger(__name__)

# Spanish day names (as stored in schedules.json) → APScheduler cron tokens.
_SPANISH_TO_CRON = {
    "lunes": "mon",
    "martes": "tue",
    "miércoles": "wed",
    "jueves": "thu",
    "viernes": "fri",
    "sábado": "sat",
    "domingo": "sun",
}

_scheduler: Optional[BackgroundScheduler] = None
_loop: Optional[asyncio.AbstractEventLoop] = None


def build_job_specs(schedules: List[dict]) -> List[dict]:
    """Translate schedule entries into cron job specs.

    Pure function (no side effects) so it can be unit-tested in isolation.
    Skips disabled entries, entries with no valid days, and malformed times.

    Returns:
        A list of dicts: {id, hour, minute, day_of_week, message}.
    """
    specs: List[dict] = []
    for index, entry in enumerate(schedules):
        if not entry.get("enabled", True):
            continue

        time_str = entry.get("time", "")
        try:
            hour, minute = (int(part) for part in time_str.split(":"))
        except (ValueError, AttributeError):
            logger.warning("Skipping schedule with invalid time: %r", time_str)
            continue

        days = [
            _SPANISH_TO_CRON[day]
            for day in entry.get("days", [])
            if day in _SPANISH_TO_CRON
        ]
        if not days:
            continue

        specs.append(
            {
                "id": f"sched-{index}",
                "hour": hour,
                "minute": minute,
                "day_of_week": ",".join(days),
                "message": entry.get("message", ""),
            }
        )
    return specs


def _fire(message: str) -> None:
    """Job body: run a dispense cycle unless one is already in progress."""
    # Imported lazily to avoid a circular import at module load time.
    import api.routes_dispense as dispense
    from api.websocket import manager

    if dispense.is_busy:
        logger.info("Scheduled dispense skipped — system busy (%s)", message)
        return

    logger.info("Scheduled dispense firing (%s)", message)
    result = dispense.perform_dispense_cycle()

    if _loop is not None:
        try:
            asyncio.run_coroutine_threadsafe(manager.broadcast(result), _loop)
        except Exception as exc:  # pragma: no cover - best-effort broadcast
            logger.debug("Scheduled broadcast failed: %s", exc)


def reschedule_jobs() -> None:
    """Rebuild all cron jobs from the currently loaded schedules.

    Safe to call when the scheduler is not running (no-op). Invoked at startup
    and after every PUT /api/schedules so edits take effect without a restart.
    """
    if _scheduler is None or not _scheduler.running:
        return

    _scheduler.remove_all_jobs()
    for spec in build_job_specs(get_schedules()):
        _scheduler.add_job(
            _fire,
            trigger=CronTrigger(
                hour=spec["hour"],
                minute=spec["minute"],
                day_of_week=spec["day_of_week"],
                timezone=utc,
            ),
            args=[spec["message"]],
            id=spec["id"],
            replace_existing=True,
            coalesce=True,
            misfire_grace_time=300,
        )
    logger.info("Auto-dispenser scheduled %d job(s)", len(_scheduler.get_jobs()))


def start(loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
    """Start the background scheduler and load jobs from current schedules."""
    global _scheduler, _loop
    _loop = loop
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone=utc)
    if not _scheduler.running:
        _scheduler.start()
    reschedule_jobs()


def shutdown() -> None:
    """Stop the background scheduler if running."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
