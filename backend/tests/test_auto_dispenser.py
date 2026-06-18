from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules import auto_dispenser


def test_build_job_specs_maps_days_to_cron():
    schedules = [
        {
            "time": "08:00",
            "days": ["lunes", "miércoles", "viernes"],
            "message": "Mañana",
            "enabled": True,
        }
    ]
    specs = auto_dispenser.build_job_specs(schedules)
    assert len(specs) == 1
    spec = specs[0]
    assert spec["hour"] == 8
    assert spec["minute"] == 0
    assert spec["day_of_week"] == "mon,wed,fri"
    assert spec["message"] == "Mañana"
    assert spec["id"] == "sched-0"


def test_build_job_specs_skips_disabled():
    schedules = [
        {"time": "08:00", "days": ["lunes"], "message": "x", "enabled": False},
    ]
    assert auto_dispenser.build_job_specs(schedules) == []


def test_build_job_specs_skips_invalid_time():
    schedules = [
        {"time": "not-a-time", "days": ["lunes"], "message": "x", "enabled": True},
    ]
    assert auto_dispenser.build_job_specs(schedules) == []


def test_build_job_specs_skips_entry_without_known_days():
    schedules = [
        {"time": "08:00", "days": ["funday"], "message": "x", "enabled": True},
    ]
    assert auto_dispenser.build_job_specs(schedules) == []


def test_build_job_specs_covers_full_week():
    schedules = [
        {
            "time": "20:00",
            "days": [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "message": "Noche",
            "enabled": True,
        }
    ]
    specs = auto_dispenser.build_job_specs(schedules)
    assert specs[0]["day_of_week"] == "mon,tue,wed,thu,fri,sat,sun"


def test_reschedule_jobs_noop_when_not_running():
    # Should not raise when the scheduler was never started.
    auto_dispenser.reschedule_jobs()


def test_start_registers_jobs_then_shutdown():
    schedules = [
        {"time": "08:00", "days": ["lunes"], "message": "x", "enabled": True},
        {"time": "20:00", "days": ["martes"], "message": "y", "enabled": True},
    ]
    import modules.scheduler as scheduler

    original = scheduler._loaded_schedules
    scheduler._loaded_schedules = schedules
    try:
        auto_dispenser.start()
        assert auto_dispenser._scheduler is not None
        assert len(auto_dispenser._scheduler.get_jobs()) == 2
    finally:
        auto_dispenser.shutdown()
        scheduler._loaded_schedules = original
