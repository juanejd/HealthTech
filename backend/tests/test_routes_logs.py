from __future__ import annotations

import pytest


def test_get_logs_returns_200(client):
    response = client.get("/api/logs")
    assert response.status_code == 200


def test_get_logs_has_events_and_total(client):
    response = client.get("/api/logs")
    data = response.json()
    assert "events" in data
    assert "total" in data


def test_get_logs_total_matches_events_count(client):
    response = client.get("/api/logs")
    data = response.json()
    assert data["total"] == len(data["events"])
