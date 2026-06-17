from __future__ import annotations

import pytest


def test_post_dispense_returns_200(client):
    response = client.post("/api/dispense")
    assert response.status_code == 200


def test_post_dispense_has_status_field(client):
    response = client.post("/api/dispense")
    data = response.json()
    assert "status" in data
    assert data["status"] in ("OK", "FAIL")


def test_post_dispense_has_extraction_detected(client):
    response = client.post("/api/dispense")
    data = response.json()
    assert "extraction_detected" in data
    assert isinstance(data["extraction_detected"], bool)


def test_post_dispense_has_timestamp(client):
    response = client.post("/api/dispense")
    data = response.json()
    assert "timestamp" in data
    assert data["timestamp"].endswith("Z")
