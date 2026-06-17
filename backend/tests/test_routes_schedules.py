from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def test_get_schedules_returns_200(client):
    response = client.get("/api/schedules")
    assert response.status_code == 200


def test_get_schedules_has_schedules_key(client):
    response = client.get("/api/schedules")
    data = response.json()
    assert "schedules" in data
    assert isinstance(data["schedules"], list)


def test_get_schedules_entry_has_required_fields(client):
    response = client.get("/api/schedules")
    data = response.json()
    if data["schedules"]:
        entry = data["schedules"][0]
        assert "time" in entry
        assert "days" in entry
        assert "message" in entry
        assert "enabled" in entry


def test_put_schedules_saves_and_returns(client, tmp_path):
    sched_file = tmp_path / "schedules.json"
    payload = {
        "schedules": [
            {
                "time": "09:00",
                "days": ["lunes"],
                "message": "Tomar pastilla.",
                "enabled": True,
            }
        ]
    }
    with patch("api.routes_schedules.SCHEDULES_FILE", sched_file):
        response = client.put("/api/schedules", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["schedules"][0]["time"] == "09:00"


def test_put_schedules_invalid_time_returns_422(client):
    payload = {
        "schedules": [
            {
                "time": "25:00",
                "days": ["lunes"],
                "message": "Tomar pastilla.",
                "enabled": True,
            }
        ]
    }
    response = client.put("/api/schedules", json=payload)
    assert response.status_code == 422


def test_put_schedules_invalid_time_format_returns_422(client):
    payload = {
        "schedules": [
            {
                "time": "not-a-time",
                "days": ["lunes"],
                "message": "Tomar pastilla.",
                "enabled": True,
            }
        ]
    }
    response = client.put("/api/schedules", json=payload)
    assert response.status_code == 422
