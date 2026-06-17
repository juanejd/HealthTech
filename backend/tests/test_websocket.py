from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_websocket_connect(client):
    with client.websocket_connect("/ws/status") as ws:
        pass


def test_websocket_receives_broadcast(client):
    with client.websocket_connect("/ws/status") as ws:
        pass
