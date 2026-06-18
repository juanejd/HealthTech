from __future__ import annotations

import pytest


def test_get_status_returns_200(client):
    response = client.get("/api/status")
    assert response.status_code == 200


def test_get_status_has_required_fields(client):
    response = client.get("/api/status")
    data = response.json()
    assert "current_day" in data
    assert "compartment_index" in data
    assert "wifi_connected" in data


def test_get_status_current_day_is_spanish(client):
    response = client.get("/api/status")
    data = response.json()
    valid_days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    assert data["current_day"] in valid_days


def test_get_status_compartment_index_is_int(client):
    response = client.get("/api/status")
    data = response.json()
    assert isinstance(data["compartment_index"], int)
    assert 0 <= data["compartment_index"] <= 6
